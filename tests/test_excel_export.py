import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


class ExcelExportTests(unittest.TestCase):
    def test_file_matches_source_and_cached_results(self):
        folder=ROOT/'dashboard/downloads';manifest=json.loads((folder/'excel-manifest.json').read_text())
        data=(folder/manifest['file']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),manifest['sha256'])
        source=json.loads((ROOT/'data/sector_source_manifest.json').read_text())
        self.assertEqual(manifest['source_sha256'],source['sha256'])
        self.assertEqual(manifest['latest_period'],source['coverage']['end'])
        expected=json.loads((ROOT/'reports/monthly'/f'{manifest["latest_period"][:7]}.json').read_text())
        with ZipFile(folder/manifest['file']) as archive:
            sheet=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
            for address,value in [('B13',expected['total']['current_gwh']),('E13',expected['total']['yoy_percent']/100),('B22',expected['ytd']['current_gwh'])]:
                cell=sheet.find(f'.//s:c[@r="{address}"]',NS)
                self.assertIsNotNone(cell.find('s:f',NS))
                self.assertAlmostEqual(float(cell.find('s:v',NS).text),value,places=5)
            self.assertIsNotNone(sheet.find('.//s:dataValidation[@sqref="B4"]',NS))
            content_types=ET.fromstring(archive.read('[Content_Types].xml'))
            chart_parts=[p.attrib['PartName'].lstrip('/') for p in content_types if p.attrib.get('ContentType')=='application/vnd.openxmlformats-officedocument.drawingml.chart+xml']
            self.assertEqual(len(chart_parts),1)
            chart=ET.fromstring(archive.read(chart_parts[0]))
            chart_ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
            formulas=[p.text.replace('$','') for p in chart.findall('.//c:f',chart_ns)]
            self.assertTrue(any('B10' in p and 'B12' in p for p in formulas))
            self.assertTrue(any('C10' in p and 'C12' in p for p in formulas))
            for name in archive.namelist():
                if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                    self.assertFalse(ET.fromstring(archive.read(name)).findall('.//s:c[@t="e"]',NS))
