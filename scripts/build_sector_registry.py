"""Read-only projection of the prospective event ledger for the public report."""
import json
from datetime import datetime,timezone
from scripts.sector_registry import ROOT,LEDGER,verified_protocol,validate_chain,assess


def build():
    protocol=verified_protocol();ledger=json.loads((ROOT/LEDGER).read_text())
    validate_chain(ledger,protocol,ROOT)
    result=assess(ledger,protocol,datetime.now(timezone.utc))
    result['ledger']=ledger
    result['method_url']='https://github.com/ignapetit25-tech/energy-demand-lab/blob/main/docs/registro-sectorial.md'
    return result


if __name__=='__main__':
    result=build()
    (ROOT/'dashboard/downloads/sector_prospective_registry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('Sector registry:',result['issued_months'],'issued months;',result['outcome_months'],'outcome months;',result['decision'])
