import gzip
import logging
from pathlib import Path
from lxml import etree
import yaml
from parse.flattener import flatten_offer

logger = logging.getLogger(__name__)

class OfferteParser:
    def __init__(self, mapping_path: Path):
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.mapping = yaml.safe_load(f)
        self.namespaces = self.mapping.get('namespaces', {})
        self.offer_tag = self.mapping.get('offer_tag')
        if not self.offer_tag:
            root_path = self.mapping.get('root_offer_path', '')
            import re
            parts = re.split(r'/(?![^{]*\})', root_path)
            self.offer_tag = parts[-1]

    def parse(self, xml_path: Path, commodity: str):
        """
        Analizza in streaming (iterparse) e delega l'appiattimento al modulo flattener.
        """
        logger.info(f"Avvio parsing in streaming di {xml_path}")
        source = gzip.open(xml_path, 'rb') if xml_path.suffix == '.gz' else str(xml_path)
        context = etree.iterparse(source, events=('end',), tag=self.offer_tag)
        
        for event, elem in context:
            offer_data = flatten_offer(elem, commodity, self.namespaces)
            if offer_data:
                yield offer_data
            
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
