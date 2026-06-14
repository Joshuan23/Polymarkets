"""Remove fake placeholder leads from the database."""
import sqlite3

FAKE_DOMAINS = [
    "quickfixauto.com", "autodocs.com", "mecanicos.com", "airco.com",
    "climatecontrol.com", "tempfix.com", "plumbingexperts.com", "drainpro.com",
    "pipefix.com", "tampadental.com", "cosmeticdental.com", "orthodental.com",
    "beautymedspa.com", "aestheticmedspa.com", "lasermedspa.com", "familymed.com",
    "primarycare.com", "internalmed.com", "tampaattorney.com", "legalservices.com",
    "lawfirm.com", "tamparealtors.com", "homefinder.com", "propertylist.com",
    "rentalproperty.com", "apartmentmanager.com", "leasingoffice.com",
    "fitnessstudio.com", "gymlife.com", "personaltrainer.com", "photostudio.com",
    "weddingphotographer.com", "portraitstudio.com", "salonbeauty.com",
    "hairdesign.com", "spaandbeauty.com", "towinghelp.com", "quicktow.com",
    "roadtowing.com", "storetampa.com", "cityretail.com", "localshop.com",
    "bizconsult.com", "strategicbiz.com", "consultingpro.com", "toproofing.com",
    "roofmasters.com", "shinglerepair.com", "greenlawns.com", "landscapepros.com",
    "yardcare.com", "pestguard.com", "bugbusters.com", "exterminate.com",
    "garageplus.com", "garagerepair.com", "doorfix.com", "electricservices.com",
    "powerline.com", "lightupgrade.com", "tampapipe.com", "fastplumber.com",
    "drainmasters.com", "reliablehvac.com", "coolmasters.com", "salon.store",
    "plumbingsupply.com",
]

conn = sqlite3.connect("leads.db")
c = conn.cursor()

total = 0
for domain in FAKE_DOMAINS:
    c.execute("DELETE FROM leads WHERE LOWER(email) LIKE LOWER(?)", (f"%@{domain}",))
    removed = c.rowcount
    if removed:
        print(f"  Removed {removed} lead(s) from {domain}")
    total += removed

conn.commit()

c.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
remaining = c.fetchone()[0]
conn.close()

print(f"\nRemoved {total} fake leads. Real leads remaining: {remaining}")
