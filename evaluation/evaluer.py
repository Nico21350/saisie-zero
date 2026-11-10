# Compare ce que la démo a extrait des 5 documents d'exemple avec les valeurs exactes.
# Les réponses de la démo sont dans evaluation/<document>.json (obtenues en envoyant chaque PDF
# au webhook, comme le fait la page). Lancer depuis la racine : python evaluation/evaluer.py

import json
from pathlib import Path

DOSSIER = Path(__file__).parent

# Valeurs exactes, recopiées des documents d'exemple (exemples/sources/*.html)
ATTENDU = {
    "facture-1-pixelvent": {
        "type_document": "facture", "emetteur.nom": "Pixelvent SRL", "emetteur.numero_tva": "BE 0712.345.631",
        "client.nom": "Boulangerie Lemaire SRL", "client.numero_tva": "BE 0659.812.708", "numero": "F-2026-0147",
        "date": "2026-10-15", "date_echeance": "2026-11-14", "date_validite": None,
        "total_htva": 3155.00, "montant_tva": 662.55, "total_tvac": 3817.55,
        "lignes": [(1, 2400.00, 21), (1, 180.00, 21), (1, 350.00, 21), (3, 75.00, 21)],
    },
    "facture-2-encres-vives": {
        "type_document": "facture", "emetteur.nom": "Les Encres Vives SRL", "emetteur.numero_tva": "BE 0834.567.116",
        "client.nom": "Atelier d'architecture Moreau & Lens SRL", "client.numero_tva": "BE 0794.532.642", "numero": "2026/0892",
        "date": "2026-10-22", "date_echeance": "2026-11-05", "date_validite": None,
        "total_htva": 554.10, "montant_tva": 79.99, "total_tvac": 634.09,
        "lignes": [(2, 89.00, 6), (1, 64.50, 6), (20, 5.40, 21), (4, 38.90, 21), (15, 3.20, 21)],
    },
    "facture-3-clim-ardenne": {
        "type_document": "facture", "emetteur.nom": "Clim'Ardenne Services SRL", "emetteur.numero_tva": "BE 0751.938.259",
        "client.nom": "Restaurant Le Petit Verger SRL", "client.numero_tva": "BE 0587.340.939", "numero": "FAC-26-0311",
        "date": "2026-10-28", "date_echeance": "2026-11-27", "date_validite": None,
        "total_htva": 897.80, "montant_tva": 188.54, "total_tvac": 1086.34,
        "lignes": [(1, 285.00, 21), (1, 412.80, 21), (2.5, 62.00, 21), (1, 45.00, 21)],
    },
    "devis-1-delvaux": {
        "type_document": "devis", "emetteur.nom": "Peintures Delvaux & Fils SRL", "emetteur.numero_tva": "BE 0462.881.526",
        "client.nom": "M. Julien Dubois", "client.numero_tva": None, "numero": "D-2026-058",
        "date": "2026-10-12", "date_echeance": None, "date_validite": "2026-11-11",
        "total_htva": 2416.50, "montant_tva": 144.99, "total_tvac": 2561.49,
        "lignes": [(85, 6.50, 6), (85, 12.00, 6), (32, 14.50, 6), (1, 380.00, 6)],
    },
    "devis-2-saveurs-de-meuse": {
        "type_document": "devis", "emetteur.nom": "Saveurs de Meuse SRL", "emetteur.numero_tva": "BE 0786.304.765",
        "client.nom": "Novalog SA", "client.numero_tva": "BE 0438.195.620", "numero": "DEV-0219",
        "date": "2026-10-20", "date_echeance": None, "date_validite": "2026-11-20",
        "total_htva": 3009.60, "montant_tva": 421.42, "total_tvac": 3431.02,
        "lignes": [(80, 24.50, 12), (10, 38.00, 12), (80, 4.50, 21), (24, 12.90, 21)],
    },
}


def lire(o, chemin):
    for morceau in chemin.split("."):
        o = (o or {}).get(morceau)
    return o


def egal(a, b):
    if isinstance(b, float) or isinstance(a, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 0.005
    return a == b


total_ok = total = 0
lignes_rapport = []
for nom, attendu in ATTENDU.items():
    reponse = json.loads((DOSSIER / f"{nom}.json").read_text(encoding="utf-8"))
    obtenu = reponse.get("output", {})
    erreurs = []
    ok = n = 0
    for champ, valeur in attendu.items():
        if champ == "lignes":
            continue
        n += 1
        if egal(lire(obtenu, champ), valeur):
            ok += 1
        else:
            erreurs.append(f"{champ} : attendu {valeur!r}, obtenu {lire(obtenu, champ)!r}")
    lignes_obtenues = obtenu.get("lignes") or []
    for i, (qte, pu, taux) in enumerate(attendu["lignes"]):
        n += 3
        l = lignes_obtenues[i] if i < len(lignes_obtenues) else {}
        for champ, valeur in (("quantite", qte), ("prix_unitaire_htva", pu), ("taux_tva", taux)):
            if egal(l.get(champ), valeur):
                ok += 1
            else:
                erreurs.append(f"ligne {i + 1} {champ} : attendu {valeur!r}, obtenu {l.get(champ)!r}")
    if len(lignes_obtenues) != len(attendu["lignes"]):
        erreurs.append(f"nombre de lignes : attendu {len(attendu['lignes'])}, obtenu {len(lignes_obtenues)}")
    total_ok += ok
    total += n
    lignes_rapport.append((nom, ok, n, reponse.get("excel"), erreurs))

for nom, ok, n, excel, erreurs in lignes_rapport:
    print(f"{nom} : {ok}/{n} champs exacts | Excel : {excel}")
    for e in erreurs:
        print(f"   - {e}")
print(f"TOTAL : {total_ok}/{total} champs exacts ({100 * total_ok / total:.1f} %)")
