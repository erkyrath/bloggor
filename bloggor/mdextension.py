
import re
import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.blockprocessors import BlockProcessor
from markdown.postprocessors import Postprocessor
import xml.etree.ElementTree as etree

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
        blocks[0] = self.RE_FENCE_START.sub('', blocks[0])

        # Find block with ending fence
        for block_num, block in enumerate(blocks):
            if self.RE_FENCE_END.search(block):
                # remove fence
                blocks[block_num] = self.RE_FENCE_END.sub('', block)
                # render fenced area inside a new div
                e = etree.SubElement(parent, 'div')
                e.set('class', 'PreWrap')
                self.parser.parseBlocks(e, blocks[0:block_num + 1])
                # remove used blocks
                for i in range(0, block_num + 1):
                    blocks.pop(0)
                return True
        # No closing marker!  Restore and do nothing
        blocks[0] = original_block
        return False  # equivalent to our test() routine returning False

class UnwrapExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(UnwrapBlockProcessor(md.parser), 'unwrap', 175)


class LocalLinkProcessor(Treeprocessor):
    RE_BLOGURL = re.compile('^https?://blog.zarfhome.com', flags=re.IGNORECASE)
    
    def run(self, root):
        # Iterate over <a> elements
        for el in root.iter('a'):
            if 'href' in el.attrib:
                match = self.RE_BLOGURL.match(el.attrib['href'])
                if match:
                    href = el.attrib['href'][ match.end() : ]
                    if href.endswith('.html'):
                        href = href[ : -5 ]
                    if not href.startswith('/'):
                        href = '/'+href
                    el.attrib['href'] = href
        # Iterate over <img> elements
        for el in root.iter('img'):
            if 'src' in el.attrib:
                match = self.RE_BLOGURL.match(el.attrib['src'])
                if match:
                    src = el.attrib['src'][ match.end() : ]
                    if not src.startswith('/'):
                        src = '/'+src
                    el.attrib['src'] = src
                    
class LocalLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(LocalLinkProcessor(md), 'locallink', 15)

