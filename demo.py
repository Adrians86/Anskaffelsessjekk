from sqlmodel import Session, SQLModel, create_engine, select
from core.models import Invoice
from core.reporting import check_invoice
from core.synth import scenario_deler

engine = create_engine("sqlite://")
SQLModel.metadata.create_all(engine)

with Session(engine) as s:
    scenario_deler.generate(s)
    for inv in s.exec(select(Invoice)).all():
        r = check_invoice(s, inv)
        print(f"\n{inv.invoice_number}: {r.verdict.value}  (verdi funnet: {r.verdi_funnet} kr)")
        for f in r.findings:
            print(f"   - {f.message}")
            print(f"     Grunnlag: {f.citation}")