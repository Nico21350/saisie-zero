// Code du bloc n8n « Vérifier la demande » (Code in JavaScript, Run Once for All Items),
// placé entre le Webhook et la lecture du PDF.

// Vérifie la demande avant l'analyse : fichier présent, vrai PDF, taille,
// et nombre d'analyses (pour protéger le quota gratuit de Gemini).
// En cas de refus, le code HTTP suit la norme : 400 (rien reçu), 413 (trop lourd),
// 415 (pas un PDF), 429 (limite atteinte).
const LIMITE_PAR_HEURE = 10; // par visiteur, remise à zéro au début de chaque heure
const LIMITE_PAR_JOUR = 100; // pour toute la démo
const TAILLE_MAX = 5 * 1024 * 1024; // 5 Mo

const item = $input.first();
const fichier = item.binary?.Document;

function refuser(message, code) {
  return [{ json: { valide: false, erreur: message, code } }];
}

if (!fichier) return refuser("Aucun fichier reçu. Choisissez un PDF.", 400);

const contenu = await this.helpers.getBinaryDataBuffer(0, 'Document');
if (contenu.length > TAILLE_MAX) return refuser("Ce fichier dépasse 5 Mo.", 413);
// Tous les vrais PDF commencent par les caractères "%PDF"
if (contenu.subarray(0, 4).toString() !== '%PDF') return refuser("Ce fichier n'est pas un vrai PDF.", 415);

// Compteurs gardés par n8n d'une exécution à l'autre (seulement quand le workflow est publié).
// Limite simple pour une démo : deux demandes exactement simultanées peuvent passer ensemble.
const memoire = $getWorkflowStaticData('global');
const heure = Math.floor(Date.now() / 3600000);
const jour = new Date().toISOString().slice(0, 10);
const visiteur = (item.json.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'local';

if (memoire.heure !== heure) { memoire.heure = heure; memoire.parVisiteur = {}; }
if (memoire.jour !== jour) { memoire.jour = jour; memoire.total = 0; }

const dejaFaites = memoire.parVisiteur[visiteur] || 0;
if (dejaFaites >= LIMITE_PAR_HEURE) return refuser(`Vous avez atteint la limite de ${LIMITE_PAR_HEURE} analyses par heure. Réessayez plus tard.`, 429);
if (memoire.total >= LIMITE_PAR_JOUR) return refuser("La démo a atteint sa limite d'analyses pour aujourd'hui. Revenez demain.", 429);

memoire.parVisiteur[visiteur] = dejaFaites + 1;
memoire.total += 1;

return [{ json: { ...item.json, valide: true }, binary: item.binary }];
