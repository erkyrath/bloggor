
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

