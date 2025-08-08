import sys
import re
import markdown
from markdown.extensions import attr_list
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import InlineProcessor
from markdown.blockprocessors import BlockProcessor
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
import xml.etree.ElementTree as etree

def extension_list(serverurl='http://localhost/'):
    # All the extensions we will use, including the ones from the module.
    return [
        'meta', 'attr_list', 'def_list', 'fenced_code', 'tables',
        CommentExtension(),
        StrikethroughExtension(),
        MoreBreakExtension(),
        UnwrapExtension(),
        DictDefInlineExtension(),
        LocalLinkExtension(serverurl),
    ]


class CommentPreProcessor(Preprocessor):
    pattern = re.compile('^;;')
    
    def run(self, lines):
        return [ ln for ln in lines if not CommentPreProcessor.pattern.match(ln) ]
    
class CommentExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CommentPreProcessor(md.parser), 'comment', 1)


class MoreBreakProcessor(BlockProcessor):
    pattern = re.compile('^[ ]*(-[ ]+)(-[ ]+)-[ ]*', re.MULTILINE)
    
    def test(self, parent, block):
        match = MoreBreakProcessor.pattern.search(block)
        if match and (match.end() == len(block) or block[match.end()] == '\n'):
            self.match = match
            return True
        self.match = None
        return False

    def run(self, parent, blocks):
        block = blocks.pop(0)
        match = self.match
        self.match = None
        etree.SubElement(parent, 'morebreak')
        postlines = block[match.end():].lstrip('\n')
        if postlines:
            blocks.insert(0, postlines)

class MorePostProcessor(Postprocessor):
    pattern = re.compile('<morebreak></morebreak>')
    
    def run(self, text):
        return MorePostProcessor.pattern.sub('<!--more-->\n<a name="more"></a>\n', text)
    
class MoreBreakExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(MoreBreakProcessor(md.parser), 'morebreak', 100)
        md.postprocessors.register(MorePostProcessor(md.parser), 'morepost', 0)


class UnwrapBlockProcessor(BlockProcessor):
    RE_FENCE_START = re.compile(r'^ *[{]{3,}( +\{(?P<attrs>[^\}\n]*)\})? *\n')
    RE_FENCE_END = re.compile(r'\n *[}]{3,}\s*$')

    def test(self, parent, block):
        return self.RE_FENCE_START.match(block)

    def run(self, parent, blocks):
        original_block = blocks[0]
        match = self.RE_FENCE_START.search(blocks[0])
        if not match:
            return False
        if match.group('attrs'):
            id, classes, config = self.handle_attrs(attr_list.get_attrs(match.group('attrs')))
        else:
            id, classes, config = '', [ 'PreWrap' ], {}
        blocks[0] = blocks[0][ : match.start() ] + blocks[0][ match.end() : ]

        # Find block with ending fence
        for block_num, block in enumerate(blocks):
            if self.RE_FENCE_END.search(block):
                # remove fence
                blocks[block_num] = self.RE_FENCE_END.sub('', block)
                # render fenced area inside a new div
                e = etree.SubElement(parent, 'div')
                if id:
                    e.set('id', id)
                e.set('class', ' '.join(classes))
                for k, v in config.items():
                    e.set(k, v)
                self.parser.parseBlocks(e, blocks[0:block_num + 1])
                # remove used blocks
                for i in range(0, block_num + 1):
                    blocks.pop(0)
                return True
            
        # No closing marker!  Restore and do nothing
        blocks[0] = original_block
        return False  # equivalent to our test() routine returning False

    def handle_attrs(self, attrs):
        id = ''
        classes = []
        configs = {}
        for k, v in attrs:
            if k == 'id':
                id = v
            elif k == '.':
                classes.append(v)
            else:
                configs[k] = v
        return id, classes, configs

class UnwrapExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(UnwrapBlockProcessor(md.parser), 'unwrap', 175)


class LocalLinkProcessor(Treeprocessor):
    def __init__(self, md=None, prefixes=[]):
        Treeprocessor.__init__(self, md=md)
        self.prefixes = prefixes
    
    def run(self, root):
        # Iterate over <a> elements
        for el in root.iter('a'):
            if 'href' in el.attrib:
                href = removeprefixes(el.attrib['href'], self.prefixes)
                if href is not None:
                    if href.endswith('.html'):
                        href = href[ : -5 ]
                    if not href.startswith('/'):
                        href = '/'+href
                    el.attrib['href'] = href
        # Iterate over <img> elements
        for el in root.iter('img'):
            if 'src' in el.attrib:
                src = removeprefixes(el.attrib['src'], self.prefixes)
                if src is not None:
                    if not src.startswith('/'):
                        src = '/'+src
                    el.attrib['src'] = src
                    
class LocalLinkExtension(Extension):
    def __init__(self, serverurl):
        Extension.__init__(self)

        val = serverurl.lower()
        if val.endswith('/'):
            val = val[ : -1 ]
        match = re.match('^https?://', val)
        val = val[ match.end() : ]
        self.prefixes = [ 'http://'+val, 'https://'+val ]
    
    def extendMarkdown(self, md):
        md.treeprocessors.register(LocalLinkProcessor(md, self.prefixes), 'locallink', 15)


class StrikethroughProcessor(InlineProcessor):
    PATTERNTEXT = r'~~(.*?)~~'
    
    def __init__(self, md=None):
        InlineProcessor.__init__(self, self.PATTERNTEXT, md)
        
    def handleMatch(self, m, data):
        el = etree.Element('s')  # <strike> is deprecated, remember
        el.text = m.group(1)
        return el, m.start(0), m.end(0)

class StrikethroughExtension(Extension):
    def extendMarkdown(self, md):
        # Just below "*" and "_"
        md.inlinePatterns.register(StrikethroughProcessor(md), 'strike', 49)

        
class DictDefInlineProcessor(InlineProcessor):
    PATTERNTEXT = r'\{\{:(.*?):\}\}'
    
    def __init__(self, md=None):
        InlineProcessor.__init__(self, self.PATTERNTEXT, md)
        
    def handleMatch(self, match, data):
        map = {}
        dat = match.group(1)
        ls = dat.split('\n')
        ls = [ val for val in ls if val.strip() ]
        while ls:
            ln = ls[0]
            key, delim, val = ln.partition(':')
            if not delim:
                break
            key = key.strip()
            val = val.strip()
            if not key and not val:
                break
            map[key] = val
            del ls[0]
        text = '\n'.join(ls)
        el = self.create_element(map, text)
        return el, match.start(0), match.end(0)

    def create_element(self, map, text):
        typ = map.pop('type', None)
        if not typ and 'img' in map:
            typ = 'img'
        if typ == 'img':
            imgsrc = map.pop('img', '#???')
            linksrc = map.pop('link', None)
            if linksrc:
                ael = etree.Element('a')
                ael.set('href', linksrc)
                el = etree.SubElement(ael, 'img')
                el.set('src', imgsrc)
                for key in map:
                    el.set(key, map[key])
                return ael
            el = etree.Element('img')
            el.set('src', imgsrc)
            for key in map:
                el.set(key, map[key])
            return el
        el = etree.Element('span')
        for key in map:
            el.set(key, map[key])
        if text:
            el.text = text
        return el

class DictDefInlineExtension(Extension):
    def extendMarkdown(self, md):
        # Just above links and images, but below \ and ``
        md.inlinePatterns.register(DictDefInlineProcessor(md), 'dictdefi', 175)

        
from bloggor.util import removeprefixes

if __name__ == '__main__':
    # For testing purposes, you can type
    #     python3 -m bloggor.mdextension test.md
    # ...and get an HTML dump of the markdown output.

    if len(sys.argv) <= 1:
        print('usage: python3 -m bloggor.mdextension TEST.MD')
        sys.exit()
    
    mdenv = markdown.Markdown(extensions=extension_list())

    for file in sys.argv[ 1 : ]:
        with open(file) as infl:
            dat = infl.read()
        mdenv.reset()
        body = mdenv.convert(dat)
        metadata = mdenv.Meta
        if metadata:
            print('metadata: %s' % (metadata,))
            print()
        print(body)
        
