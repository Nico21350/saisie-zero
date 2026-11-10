# Fabrique le classeur Excel de Saisie Zéro : excel/saisie-zero-documents.xlsx
# Lancer depuis la racine du projet : python excel/creer-classeur.py
#
# Feuille « Documents » : un tableau Excel nommé « Documents ». n8n y ajoute une ligne par PDF
# (colonnes brutes). Les colonnes calculées (Statut, Taux TVA moyen, Contrôle TVA, Jours restants)
# sont des formules du tableau : Excel les recopie seul sur chaque nouvelle ligne.
# Les 5 lignes de départ sont les documents d'exemple fictifs du dossier exemples/.

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableFormula, TableStyleInfo

SORTIE = Path(__file__).with_name("saisie-zero-documents.xlsx")

POLICE = "Arial"
INDIGO = "5B5BF0"
INDIGO_DOUX = "E8E8FD"
TURQUOISE = "0F9C8C"
TURQUOISE_DOUX = "DDF5F1"
ENCRE = "141827"
DISCRET = "5D6478"
VERT, VERT_DOUX = "0F8A68", "DCF3EA"
ROUGE, ROUGE_DOUX = "C0262D", "FBE1E2"
ORANGE, ORANGE_DOUX = "B45309", "FDEBD3"
GRIS, GRIS_DOUX = "5D6478", "ECEEF3"
CALCULE = "F4F5F9"  # fond des colonnes calculées

FORMAT_DATE = "dd\/mm\/yyyy"
FORMAT_EUROS = '#,##0.00 "€";-#,##0.00 "€";"-"'


def ligne(nom):
    """Référence à une colonne du tableau, sur la ligne courante (forme stockée dans le fichier)."""
    return f"Documents[[#This Row],[{nom}]]"


# Colonne de référence pour l'échéance : la validité pour un devis, l'échéance pour une facture.
REF_DATE = f'IF({ligne("Type")}="devis",{ligne("Validité")},{ligne("Échéance")})'

# (titre, largeur, format, formule ou None pour une colonne remplie par n8n)
COLONNES = [
    ("Traité le", 19, "dd\/mm\/yyyy hh:mm", None),
    ("Type", 12, None, None),
    ("Statut", 14, None,
     f'=IF({ligne("Type")}="facture",IF({ligne("Jours restants")}="","À vérifier",'
     f'IF({ligne("Jours restants")}<0,"En retard","À payer")),'
     f'IF({ligne("Type")}="devis",IF({ligne("Jours restants")}="","À vérifier",'
     f'IF({ligne("Jours restants")}<0,"Expiré","Valable")),"À vérifier"))'),
    ("Numéro", 15, None, None),
    ("Date", 13, FORMAT_DATE, None),
    ("Échéance", 14, FORMAT_DATE, None),
    ("Validité", 13, FORMAT_DATE, None),
    ("Émetteur", 32, None, None),
    ("TVA émetteur", 18, None, None),
    ("Client", 42, None, None),
    ("TVA client", 17, None, None),
    ("Total HTVA", 16, FORMAT_EUROS, None),
    ("TVA", 13, FORMAT_EUROS, None),
    ("Total TVAC", 16, FORMAT_EUROS, None),
    ("Taux TVA moyen", 20, "0.0%", f'=IFERROR({ligne("TVA")}/{ligne("Total HTVA")},"")'),
    ("Contrôle TVA", 17, None,
     f'=IF(OR({ligne("Total TVAC")}="",{ligne("Total HTVA")}=""),"",'
     f'IF(ABS({ligne("Total HTVA")}+{ligne("TVA")}-{ligne("Total TVAC")})<0.02,"OK","Écart"))'),
    ("Jours restants", 18, '0" j";-0" j";"0 j"',
     f'=IFERROR(IF({REF_DATE}="","",{REF_DATE}-TODAY()),"")'),
    ("Nb lignes", 13, "0", None),
    ("Fichier", 30, None, None),
    ("Lignes", 210, None, None),
]

d = datetime
EXEMPLES = [
    [d(2026, 11, 10, 9, 2), "facture", "F-2026-0147", d(2026, 10, 15), d(2026, 11, 14), None,
     "Pixelvent SRL", "BE 0712.345.631", "Boulangerie Lemaire SRL", "BE 0659.812.708",
     3155.00, 662.55, 3817.55, 4,
     "1 x Refonte du site vitrine (forfait) à 2400 € (TVA 21 %) / 1 x Hébergement annuel à 180 € (TVA 21 %) / "
     "1 x Séance photos produits (demi-journée) à 350 € (TVA 21 %) / 3 x Formation à la gestion du site (heures) à 75 € (TVA 21 %)",
     "facture-1-pixelvent.pdf"],
    [d(2026, 11, 10, 9, 5), "facture", "2026/0892", d(2026, 10, 22), d(2026, 11, 5), None,
     "Les Encres Vives SRL", "BE 0834.567.116", "Atelier d'architecture Moreau & Lens SRL", "BE 0794.532.642",
     554.10, 79.99, 634.09, 5,
     "2 x Code civil annoté 2026 à 89 € (TVA 6 %) / 1 x Ouvrage « Droit de la construction » à 64.5 € (TVA 6 %) / "
     "20 x Ramette papier A4 500 f. à 5.4 € (TVA 21 %) / 4 x Cartouche d'encre à 38.9 € (TVA 21 %) / "
     "15 x Classeur à levier à 3.2 € (TVA 21 %)",
     "facture-2-encres-vives.pdf"],
    [d(2026, 11, 10, 9, 8), "facture", "FAC-26-0311", d(2026, 10, 28), d(2026, 11, 27), None,
     "Clim'Ardenne Services SRL", "BE 0751.938.259", "Restaurant Le Petit Verger SRL", "BE 0587.340.939",
     897.80, 188.54, 1086.34, 4,
     "1 x Entretien annuel chambre froide à 285 € (TVA 21 %) / 1 x Ventilateur de condenseur (pièce) à 412.8 € (TVA 21 %) / "
     "2.5 x Main-d'œuvre (h) à 62 € (TVA 21 %) / 1 x Frais de déplacement à 45 € (TVA 21 %)",
     "facture-3-clim-ardenne.pdf"],
    [d(2026, 11, 10, 9, 11), "devis", "D-2026-058", d(2026, 10, 12), None, d(2026, 11, 11),
     "Peintures Delvaux & Fils SRL", "BE 0462.881.526", "M. Julien Dubois", None,
     2416.50, 144.99, 2561.49, 4,
     "85 x Préparation murs et plafonds (ponçage, rebouchage) à 6.5 € (TVA 6 %) / 85 x Peinture murs, 2 couches à 12 € (TVA 6 %) / "
     "32 x Peinture plafonds à 14.5 € (TVA 6 %) / 1 x Fournitures (peinture, bâches, protections) à 380 € (TVA 6 %)",
     "devis-1-delvaux.pdf"],
    [d(2026, 11, 10, 9, 14), "devis", "DEV-0219", d(2026, 10, 20), None, d(2026, 11, 20),
     "Saveurs de Meuse SRL", "BE 0786.304.765", "Novalog SA", "BE 0438.195.620",
     3009.60, 421.42, 3431.02, 4,
     "80 x Buffet froid (par personne) à 24.5 € (TVA 12 %) / 10 x Service en salle (2 serveurs × 5 h) à 38 € (TVA 12 %) / "
     "80 x Forfait boissons sans alcool (par personne) à 4.5 € (TVA 21 %) / 24 x Vin, bouteille à 12.9 € (TVA 21 %)",
     "devis-2-saveurs-de-meuse.pdf"],
]

fin = Side(style="thin", color="D9DCE6")


def police(**kw):
    kw.setdefault("name", POLICE)
    kw.setdefault("color", ENCRE)
    return Font(**kw)


wb = Workbook()

# ---------------------------------------------------------------- Documents
ws = wb.active
ws.title = "Documents"
ws.sheet_view.showGridLines = False
ws.sheet_properties.tabColor = INDIGO

ws["A1"] = "Saisie Zéro : documents extraits"
ws["A1"].font = police(size=18, bold=True, color=INDIGO)
ws["A2"] = ("Chaque facture ou devis déposé sur la démo est lu par l'IA (Gemini) et ajouté ici par n8n. "
            "Les colonnes sur fond gris sont calculées par Excel.")
ws["A2"].font = police(size=10, color=DISCRET)
ws.row_dimensions[1].height = 36
ws.row_dimensions[2].height = 18
ws["A1"].alignment = Alignment(vertical="center")

ENTETE = 4
# Même hauteur pour toutes les lignes, y compris celles que n8n ajoutera (hauteur par défaut de la feuille)
HAUTEUR_LIGNE = 22
ws.sheet_format.defaultRowHeight = HAUTEUR_LIGNE
ws.sheet_format.customHeight = True
noms = [c[0] for c in COLONNES]
for j, (nom, largeur, fmt, formule) in enumerate(COLONNES, start=1):
    lettre = ws.cell(ENTETE, j).column_letter
    ws.column_dimensions[lettre].width = largeur
    ws.cell(ENTETE, j, nom)

valeurs_brutes = [c for c in COLONNES if c[3] is None]
for i, donnees in enumerate(EXEMPLES, start=ENTETE + 1):
    donnees = donnees[:-2] + [donnees[-1], donnees[-2]]  # Fichier avant Lignes
    it = iter(donnees)
    for j, (nom, largeur, fmt, formule) in enumerate(COLONNES, start=1):
        cellule = ws.cell(i, j)
        cellule.value = formule if formule else next(it)
        cellule.font = police(size=10)
        cellule.alignment = Alignment(vertical="center", wrap_text=False)
        if fmt:
            cellule.number_format = fmt
        if formule:
            cellule.fill = PatternFill("solid", fgColor=CALCULE)
            cellule.alignment = Alignment(horizontal="center", vertical="center")
        if nom in ("Type", "Nb lignes"):
            cellule.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[i].height = HAUTEUR_LIGNE

derniere = ENTETE + len(EXEMPLES)
derniere_col = ws.cell(ENTETE, len(COLONNES)).column_letter
tableau = Table(displayName="Documents", ref=f"A{ENTETE}:{derniere_col}{derniere}")
tableau.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
tableau._initialise_columns()
for colonne, (nom, largeur, fmt, formule) in zip(tableau.tableColumns, COLONNES):
    colonne.name = nom
    if formule:
        colonne.calculatedColumnFormula = TableFormula(attr_text=formule[1:])  # sans le signe =
ws.add_table(tableau)

for j in range(1, len(COLONNES) + 1):
    c = ws.cell(ENTETE, j)
    c.font = police(size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=INDIGO)
    c.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[ENTETE].height = 28
ws.freeze_panes = f"A{ENTETE + 1}"

# Couleurs automatiques (jusqu'à la ligne 5000 pour couvrir les lignes ajoutées plus tard)
def colorer(colonne, valeur, texte, fond):
    plage = f"{colonne}{ENTETE + 1}:{colonne}5000"
    ws.conditional_formatting.add(plage, FormulaRule(
        formula=[f'{colonne}{ENTETE + 1}="{valeur}"'],
        font=Font(name=POLICE, bold=True, color=texte),
        fill=PatternFill("solid", fgColor=fond, bgColor=fond)))

lettre = {nom: ws.cell(ENTETE, j).column_letter for j, nom in enumerate(noms, start=1)}
colorer(lettre["Type"], "facture", INDIGO, INDIGO_DOUX)
colorer(lettre["Type"], "devis", TURQUOISE, TURQUOISE_DOUX)
colorer(lettre["Statut"], "En retard", ROUGE, ROUGE_DOUX)
colorer(lettre["Statut"], "À payer", ORANGE, ORANGE_DOUX)
colorer(lettre["Statut"], "Valable", VERT, VERT_DOUX)
colorer(lettre["Statut"], "Expiré", GRIS, GRIS_DOUX)
colorer(lettre["Statut"], "À vérifier", ROUGE, ROUGE_DOUX)
colorer(lettre["Contrôle TVA"], "OK", VERT, VERT_DOUX)
colorer(lettre["Contrôle TVA"], "Écart", ROUGE, ROUGE_DOUX)

# ---------------------------------------------------------------- Tableau de bord
tb = wb.create_sheet("Tableau de bord", 0)
tb.sheet_view.showGridLines = False
tb.sheet_properties.tabColor = TURQUOISE
for col, largeur in zip("ABCDEFGHI", (2, 26, 22, 22, 3, 26, 22, 22, 2)):
    tb.column_dimensions[col].width = largeur

tb["B1"] = "Saisie Zéro : tableau de bord"
tb["B1"].font = police(size=18, bold=True, color=INDIGO)
tb["B2"] = "Aujourd'hui :"
tb["B2"].font = police(size=10, color=DISCRET)
tb["C2"] = "=TODAY()"
tb["C2"].number_format = FORMAT_DATE
tb["C2"].font = police(size=10, bold=True, color=DISCRET)
tb["C2"].alignment = Alignment(horizontal="left")
tb.row_dimensions[1].height = 36
tb["B1"].alignment = Alignment(vertical="center")
for r in (4, 7, 10, 19):
    tb.row_dimensions[r].height = 24

T = "Documents"
TUILES = [  # (ligne, colonne, titre, formule, format, couleur)
    (4, "B", "Documents analysés", f"=COUNTA({T}[Type])", "0", INDIGO),
    (4, "C", "Factures", f'=COUNTIF({T}[Type],"facture")', "0", INDIGO),
    (4, "D", "Devis", f'=COUNTIF({T}[Type],"devis")', "0", TURQUOISE),
    (4, "F", "Total facturé TVAC", f'=SUMIFS({T}[Total TVAC],{T}[Type],"facture")', FORMAT_EUROS, INDIGO),
    (4, "G", "dont TVA", f'=SUMIFS({T}[TVA],{T}[Type],"facture")', FORMAT_EUROS, INDIGO),
    (4, "H", "Devis valables TVAC", f'=SUMIFS({T}[Total TVAC],{T}[Statut],"Valable")', FORMAT_EUROS, TURQUOISE),
    (7, "B", "Factures en retard", f'=COUNTIF({T}[Statut],"En retard")', "0", ROUGE),
    (7, "C", "Montant en retard", f'=SUMIFS({T}[Total TVAC],{T}[Statut],"En retard")', FORMAT_EUROS, ROUGE),
    (7, "D", "Écarts de TVA", f'=COUNTIF({T}[Contrôle TVA],"Écart")', "0", ROUGE),
    (7, "F", "Factures à payer", f'=COUNTIF({T}[Statut],"À payer")', "0", ORANGE),
    (7, "G", "Montant à payer", f'=SUMIFS({T}[Total TVAC],{T}[Statut],"À payer")', FORMAT_EUROS, ORANGE),
    (7, "H", "Prochaine échéance",
     f'=IFERROR(SMALL({T}[Échéance],COUNTIF({T}[Échéance],"<"&TODAY())+1),"Aucune")', FORMAT_DATE, ORANGE),
]
for r, c, titre, formule, fmt, couleur in TUILES:
    haut, bas = tb[f"{c}{r}"], tb[f"{c}{r + 1}"]
    haut.value, bas.value = titre, formule
    haut.font = police(size=9, bold=True, color=DISCRET)
    bas.font = police(size=15, bold=True, color=couleur)
    bas.number_format = fmt
    for cel in (haut, bas):
        cel.fill = PatternFill("solid", fgColor="F7F8FC")
        cel.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    haut.border = Border(top=Side(style="thick", color=couleur), left=fin, right=fin)
    bas.border = Border(bottom=fin, left=fin, right=fin)
    tb.row_dimensions[r + 1].height = 30


def entete_bloc(r, c1, titres):
    for k, titre in enumerate(titres):
        cel = tb.cell(r, c1 + k, titre)
        cel.font = police(size=10, bold=True, color="FFFFFF")
        cel.fill = PatternFill("solid", fgColor=INDIGO)
        cel.alignment = Alignment(horizontal="center" if k else "left", vertical="center", indent=0 if k else 1)


# Par statut
tb["B10"] = "Par statut"
tb["B10"].font = police(size=12, bold=True, color=INDIGO)
entete_bloc(11, 2, ["Statut", "Nombre", "Montant TVAC"])
for k, statut in enumerate(["À payer", "En retard", "Valable", "Expiré", "À vérifier"]):
    r = 12 + k
    tb.cell(r, 2, statut).font = police(size=10)
    tb.cell(r, 3, f'=COUNTIF({T}[Statut],B{r})').number_format = "0"
    tb.cell(r, 4, f'=SUMIFS({T}[Total TVAC],{T}[Statut],B{r})').number_format = FORMAT_EUROS
    for col in (2, 3, 4):
        cel = tb.cell(r, col)
        cel.font = police(size=10)
        cel.border = Border(bottom=fin)
        cel.alignment = Alignment(horizontal="right" if col > 2 else "left", indent=0 if col > 2 else 1)

# Par mois (6 derniers mois, selon la date du document)
tb["F10"] = "Par mois (date du document)"
tb["F10"].font = police(size=12, bold=True, color=INDIGO)
entete_bloc(11, 6, ["Mois", "Factures TVAC", "Devis TVAC"])
for k in range(6):
    r, recul = 12 + k, 5 - k
    tb.cell(r, 6, f"=DATE(YEAR(TODAY()),MONTH(TODAY())-{recul},1)").number_format = "mmmm yyyy"
    debut, suite = f"F{r}", f"EDATE(F{r},1)"
    tb.cell(r, 7, f'=SUMIFS({T}[Total TVAC],{T}[Type],"facture",{T}[Date],">="&{debut},{T}[Date],"<"&{suite})')
    tb.cell(r, 8, f'=SUMIFS({T}[Total TVAC],{T}[Type],"devis",{T}[Date],">="&{debut},{T}[Date],"<"&{suite})')
    for col in (6, 7, 8):
        cel = tb.cell(r, col)
        cel.font = police(size=10)
        cel.border = Border(bottom=fin)
        if col > 6:
            cel.number_format = FORMAT_EUROS
        cel.alignment = Alignment(horizontal="right" if col > 6 else "left", indent=0 if col > 6 else 1)

graphique = BarChart()
graphique.type = "col"
graphique.title = None
graphique.x_axis.delete = False
graphique.y_axis.delete = False
graphique.y_axis.numFmt = "#,##0"
graphique.y_axis.majorGridlines = None
graphique.add_data(Reference(tb, min_col=7, max_col=8, min_row=11, max_row=17), titles_from_data=True)
graphique.set_categories(Reference(tb, min_col=6, min_row=12, max_row=17))
graphique.height, graphique.width = 9, 27
graphique.legend.position = "b"
graphique.legend.overlay = False
for serie, couleur in zip(graphique.series, (INDIGO, TURQUOISE)):
    serie.graphicalProperties.solidFill = couleur
    serie.graphicalProperties.line.solidFill = couleur
tb["B19"] = "Montants TVAC par mois"
tb["B19"].font = police(size=12, bold=True, color=INDIGO)
tb.add_chart(graphique, "B20")

# ---------------------------------------------------------------- À propos
ap = wb.create_sheet("À propos")
ap.sheet_view.showGridLines = False
ap.sheet_properties.tabColor = GRIS
ap.column_dimensions["A"].width = 2
ap.column_dimensions["B"].width = 24
ap.column_dimensions["C"].width = 100
ap.row_dimensions[1].height = 36
ap["B1"].alignment = Alignment(vertical="center")
ap["B1"] = "À propos de ce classeur"
ap["B1"].font = police(size=18, bold=True, color=INDIGO)
lignes_ap = [
    ("D'où viennent les données", "Un visiteur dépose un PDF sur la démo Saisie Zéro. n8n en extrait le texte, Gemini reconnaît "
     "le type de document et ses informations, puis n8n ajoute une ligne dans la feuille Documents."),
    ("Colonnes calculées", "Statut, Taux TVA moyen, Contrôle TVA et Jours restants sont des formules Excel, recopiées "
     "automatiquement sur chaque nouvelle ligne du tableau."),
    ("Statut", "Facture : À payer, ou En retard si l'échéance est passée. Devis : Valable, ou Expiré si la date de "
     "validité est passée. À vérifier : date ou type manquant."),
    ("Contrôle TVA", "Vérifie que Total HTVA + TVA = Total TVAC (à 2 centimes près). Un écart signale une erreur de "
     "lecture ou une facture mal calculée."),
    ("Tableau de bord", "Totaux, retards et montants par mois, mis à jour seuls à chaque nouvelle ligne."),
    ("Documents fictifs", "Toutes les entreprises, personnes et numéros de TVA sont inventés. N'envoyez jamais de vrais "
     "documents sur la démo."),
]
for k, (titre, texte) in enumerate(lignes_ap):
    r = 3 + k
    ap.cell(r, 2, titre).font = police(size=10, bold=True, color=INDIGO)
    ap.cell(r, 3, texte).font = police(size=10)
    ap.cell(r, 2).alignment = Alignment(vertical="top", wrap_text=True)
    ap.cell(r, 3).alignment = Alignment(wrap_text=True, vertical="top")
    ap.row_dimensions[r].height = 40

wb.active = 0
wb.save(SORTIE)
print(f"Classeur créé : {SORTIE}")
