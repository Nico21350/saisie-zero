// Code du bloc n8n « Préparer la ligne Excel » (Code in JavaScript, Run Once for All Items),
// placé entre « Facture ou devis ? » et « Ajouter dans Excel ».
//
// Le classeur est public : on nettoie tout ce que l'IA a extrait avant de l'y écrire.
// - Un texte qui commence par = + - ou @ serait lu par Excel comme une formule
//   (par exemple =HYPERLINK(...) caché dans un PDF piégé) : ces caractères sont retirés.
// - Les textes sont raccourcis, les dates gardées seulement au format AAAA-MM-JJ,
//   les montants seulement s'ils sont des nombres.
// - Le nom du fichier peut contenir des données personnelles : il n'est gardé que pour
//   les documents d'exemple de la démo.

const EXEMPLES = [
  'facture-1-pixelvent.pdf',
  'facture-2-encres-vives.pdf',
  'facture-3-clim-ardenne.pdf',
  'devis-1-delvaux.pdf',
  'devis-2-saveurs-de-meuse.pdf',
];

function texte(valeur, max = 120) {
  if (typeof valeur !== 'string') return null;
  let t = valeur.replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
  while (/^[=+\-@]/.test(t)) t = t.slice(1).trim();
  return t ? t.slice(0, max) : null;
}
const nombre = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const date = (v) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null);
const partie = (p) => ({ nom: texte(p?.nom, 100), numero_tva: texte(p?.numero_tva, 30) });

const o = $input.first().json.output || {};
const lignes = (Array.isArray(o.lignes) ? o.lignes : []).slice(0, 50).map((l) => ({
  designation: texte(l?.designation, 100),
  quantite: nombre(l?.quantite),
  prix_unitaire_htva: nombre(l?.prix_unitaire_htva),
  taux_tva: nombre(l?.taux_tva),
}));

const nomFichier = $('Webhook').first().binary?.Document?.fileName || '';

return [{
  json: {
    output: {
      type_document: o.type_document,
      emetteur: partie(o.emetteur),
      client: partie(o.client),
      numero: texte(o.numero, 40),
      date: date(o.date),
      date_echeance: date(o.date_echeance),
      date_validite: date(o.date_validite),
      lignes,
      total_htva: nombre(o.total_htva),
      montant_tva: nombre(o.montant_tva),
      total_tvac: nombre(o.total_tvac),
    },
    fichier: EXEMPLES.includes(nomFichier) ? nomFichier : 'Document déposé',
    lignesTexte: texte(
      lignes.map((l) => `${l.quantite ?? '?'} x ${l.designation ?? '?'} à ${l.prix_unitaire_htva ?? '?'} € (TVA ${l.taux_tva ?? '?'} %)`).join(' / '),
      1000,
    ),
  },
}];
