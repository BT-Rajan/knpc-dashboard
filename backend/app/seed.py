"""
Seeds the item catalog on first boot. Sources are seeded with reasonable
starting points (Yahoo Finance chart JSON for the liquid futures, since it's
free and stable) but are just rows in the `sources` table — admins are meant
to add/replace/tune these from the admin panel, not edit code.
"""
from app.db import SessionLocal
from app.models import Item, Source, ScrapeSetting
from app.config import SEED_CATALOG, DEFAULT_SCRAPE_FREQUENCY_MINUTES

# Yahoo Finance chart endpoint returns JSON; the last close lives at
# chart.result.0.meta.regularMarketPrice
YAHOO_JSON_PATH = "chart.result.0.meta.regularMarketPrice"
YAHOO_TICKERS = {
    "BRENT": "BZ=F",
    "WTI": "CL=F",
    "OMAN": "OMN=F",
}


def seed():
    db = SessionLocal()
    try:
        if not db.query(ScrapeSetting).first():
            db.add(ScrapeSetting(frequency_minutes=DEFAULT_SCRAPE_FREQUENCY_MINUTES))

        for category, items in SEED_CATALOG.items():
            for spec in items:
                existing = db.query(Item).filter(Item.code == spec["code"]).first()
                if existing:
                    continue
                item = Item(code=spec["code"], name=spec["name"], category=category, unit=spec["unit"])
                db.add(item)
                db.flush()

                ticker = YAHOO_TICKERS.get(spec["code"])
                if ticker:
                    db.add(Source(
                        item_id=item.id,
                        name="Yahoo Finance",
                        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d",
                        source_type="json_path",
                        value_selector=YAHOO_JSON_PATH,
                        priority=1,
                    ))
                # Items without a seeded ticker (Dubai, KEC, refined products)
                # ship with no source — admin adds one via the panel. This is
                # intentional: guessing a scrape target for a paywalled/absent
                # public feed produces silent bad data, which is worse than an
                # explicit "no source configured" log entry.

        db.commit()
    finally:
        db.close()
