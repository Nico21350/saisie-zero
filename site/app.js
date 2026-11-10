const config = window.SAISIE_ZERO_CONFIG;

const TAILLE_MAX = 5 * 1024 * 1024; // 5 Mo
const DELAI_MAX = 120 * 1000; // Gemini peut mettre jusqu'à une minute quand il est saturé

const EXEMPLES = [
  { fichier: "facture-1-pixelvent.pdf", nom: "Pixelvent SRL", type: "facture", numero: "Facture F-2026-0147" },
  { fichier: "facture-2-encres-vives.pdf", nom: "Les Encres Vives SRL", type: "facture", numero: "Facture 2026/0892" },
  { fichier: "facture-3-clim-ardenne.pdf", nom: "Clim'Ardenne Services SRL", type: "facture", numero: "Facture FAC-26-0311" },
  { fichier: "devis-1-delvaux.pdf", nom: "Peintures Delvaux & Fils SRL", type: "devis", numero: "Devis D-2026-058" },
  { fichier: "devis-2-saveurs-de-meuse.pdf", nom: "Saveurs de Meuse SRL", type: "devis", numero: "Offre DEV-0219" },
];

// Icônes de la zone de dépôt (texte fixe écrit ici, jamais de données venant de l'extérieur)
const ICONES = {
  attente: '<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M12 17v-6m0 0-2.5 2.5M12 11l2.5 2.5"/></svg>',
  chargement: '<div class="roue"></div>',
  termine: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/></svg>',
  erreur: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/><path d="M12 16.5h.01"/></svg>',
};

const euros = new Intl.NumberFormat("fr-BE", { style: "currency", currency: "EUR" });
const nombres = new Intl.NumberFormat("fr-BE");

const zoneDepot = document.getElementById("zone-depot");
const zoneIcone = document.getElementById("zone-icone");
const zoneTitre = document.getElementById("zone-titre");
const zoneAide = document.getElementById("zone-aide");
const aideInitiale = zoneAide.innerHTML;
const champFichier = document.getElementById("champ-fichier");
const listeExemples = document.getElementById("liste-exemples");
const voileDepot = document.getElementById("voile-depot");
const blocResultat = document.getElementById("resultat");

let analyseEnCours = false;
let compteurSecondes = null;

// --- Mise en forme des valeurs ---

function formaterMontant(valeur) {
  return typeof valeur === "number" ? euros.format(valeur) : "Non indiqué";
}

// "2026-10-15" devient "15/10/2026"
function formaterDate(iso) {
  if (!iso) return "Non indiquée";
  const morceaux = iso.split("-");
  return morceaux.length === 3 ? `${morceaux[2]}/${morceaux[1]}/${morceaux[0]}` : iso;
}

// --- Zone de dépôt : elle montre où en est l'analyse ---

function arreterCompteur() {
  clearInterval(compteurSecondes);
  compteurSecondes = null;
}

function majZone(etat, titre, aide) {
  zoneDepot.dataset.etat = etat;
  zoneIcone.innerHTML = ICONES[etat];
  zoneTitre.textContent = titre;
  if (aide === undefined) {
    zoneAide.innerHTML = aideInitiale;
  } else {
    zoneAide.textContent = aide;
  }
}

function afficherAttente() {
  arreterCompteur();
  majZone("attente", "Glissez votre PDF ici");
}

function afficherChargement(nomFichier) {
  blocResultat.hidden = true;
  majZone("chargement", `Analyse de « ${nomFichier} » en cours`, "");

  // Étapes affichées pendant l'attente. Attention : la page ne reçoit aucune nouvelle de n8n avant la
  // réponse finale. Les étapes avancent donc selon le temps écoulé (durées typiques observées),
  // pas selon l'avancement réel ; la dernière ne se coche qu'une fois la réponse reçue.
  const ETAPES = [
    { texte: "Envoi du PDF", jusqua: 2 },
    { texte: "Lecture du texte", jusqua: 5 },
    { texte: "Analyse par Gemini", jusqua: Infinity },
    { texte: "Ajout dans Excel", jusqua: Infinity },
  ];
  const liste = document.createElement("ol");
  liste.className = "etapes-analyse";
  const elements = ETAPES.map((etape) => {
    const li = document.createElement("li");
    li.textContent = etape.texte;
    liste.append(li);
    return li;
  });
  const compteur = document.createElement("span");
  compteur.className = "etapes-analyse__temps";
  zoneAide.replaceChildren(liste, compteur);

  const debut = Date.now();
  const majAide = () => {
    const secondes = Math.round((Date.now() - debut) / 1000);
    const enCours = ETAPES.findIndex((etape) => secondes < etape.jusqua);
    elements.forEach((li, i) => {
      li.className = i < enCours ? "fait" : i === enCours ? "en-cours" : "";
    });
    compteur.textContent = `${secondes} s écoulées, en général 15 à 60 secondes.`;
  };
  majAide();
  arreterCompteur();
  compteurSecondes = setInterval(majAide, 1000);

  zoneDepot.scrollIntoView({ behavior: "smooth", block: "center" });
}

function afficherErreur(message) {
  arreterCompteur();
  blocResultat.hidden = true;
  majZone("erreur", message, "Cliquez ou glissez un autre PDF pour réessayer.");
}

function afficherTermine(nomFichier) {
  arreterCompteur();
  majZone("termine", `« ${nomFichier} » analysé`, "Cliquez ou glissez un autre PDF pour recommencer.");
}

// --- Résultat ---

// On construit tout avec textContent : le texte vient de l'IA et ne doit jamais être interprété comme du HTML.
function ajouterLigneDefinition(liste, terme, valeur, classe) {
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = terme;
  dd.textContent = valeur;
  if (classe) {
    dt.classList.add(classe);
    dd.classList.add(classe);
  }
  liste.append(dt, dd);
}

function remplirPartie(prefixe, partie) {
  document.getElementById(`${prefixe}-nom`).textContent = (partie && partie.nom) || "Non indiqué";
  document.getElementById(`${prefixe}-tva`).textContent =
    partie && partie.numero_tva ? `TVA ${partie.numero_tva}` : "Pas de numéro de TVA";
}

function afficherResultat(doc) {
  const badge = document.getElementById("resultat-type");
  const libellesType = { facture: "Facture reconnue", devis: "Devis reconnu" };
  badge.textContent = libellesType[doc.type_document] || "Document non reconnu";
  badge.classList.toggle("inconnu", !libellesType[doc.type_document]);

  document.getElementById("resultat-numero").textContent = doc.numero ? `N° ${doc.numero}` : "Sans numéro";

  const meta = document.getElementById("resultat-meta");
  meta.replaceChildren();
  const groupe = (terme, valeur) => {
    const div = document.createElement("div");
    ajouterLigneDefinition(div, terme, valeur);
    meta.append(div);
  };
  groupe("Date", formaterDate(doc.date));
  if (doc.type_document === "devis") {
    groupe("Valable jusqu'au", formaterDate(doc.date_validite));
  } else {
    groupe("Échéance", formaterDate(doc.date_echeance));
  }

  remplirPartie("resultat-emetteur", doc.emetteur);
  remplirPartie("resultat-client", doc.client);

  const lignes = document.getElementById("resultat-lignes");
  lignes.replaceChildren();
  for (const ligne of doc.lignes || []) {
    const tr = document.createElement("tr");
    const cellules = [
      [ligne.designation, ""],
      [typeof ligne.quantite === "number" ? nombres.format(ligne.quantite) : "", "nombre"],
      [formaterMontant(ligne.prix_unitaire_htva), "nombre"],
      [typeof ligne.taux_tva === "number" ? `${nombres.format(ligne.taux_tva)} %` : "", "nombre"],
    ];
    for (const [texte, classe] of cellules) {
      const td = document.createElement("td");
      td.textContent = texte;
      if (classe) td.className = classe;
      tr.append(td);
    }
    lignes.append(tr);
  }

  const totaux = document.getElementById("resultat-totaux");
  totaux.replaceChildren();
  ajouterLigneDefinition(totaux, "Total HTVA", formaterMontant(doc.total_htva));
  ajouterLigneDefinition(totaux, "TVA", formaterMontant(doc.montant_tva));
  ajouterLigneDefinition(totaux, "Total TVAC", formaterMontant(doc.total_tvac), "total-final");

  const lienTableur = document.getElementById("lien-tableur");
  if (config.sheetUrl) {
    document.getElementById("lien-tableur-a").href = config.sheetUrl;
    lienTableur.hidden = false;
  }

  blocResultat.hidden = false;
  revelerResultat(doc.total_tvac);
  blocResultat.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Les morceaux du résultat apparaissent l'un après l'autre (délai en CSS via --i),
// puis le total TVAC défile de 0 jusqu'à sa valeur.
const mouvementReduit = window.matchMedia("(prefers-reduced-motion: reduce)");

function revelerResultat(totalTvac) {
  const morceaux = [
    blocResultat.querySelector(".resultat__entete"),
    document.getElementById("lien-tableur"),
    ...blocResultat.querySelectorAll(".partie"),
    ...blocResultat.querySelectorAll("thead tr, #resultat-lignes tr"),
    document.getElementById("resultat-totaux"),
  ].filter((el) => el && !el.hidden);

  blocResultat.classList.remove("revele");
  void blocResultat.offsetWidth; // relance l'animation si un résultat était déjà affiché
  morceaux.forEach((el, i) => {
    el.classList.add("revele-morceau");
    el.style.setProperty("--i", i);
  });
  blocResultat.classList.add("revele");

  const cible = blocResultat.querySelector("#resultat-totaux dd.total-final");
  if (!cible || typeof totalTvac !== "number" || mouvementReduit.matches) return;
  const depart = performance.now() + morceaux.length * 70 + 150;
  const duree = 900;
  cible.textContent = formaterMontant(0);
  const etape = (maintenant) => {
    const t = Math.min(Math.max((maintenant - depart) / duree, 0), 1);
    const adouci = 1 - Math.pow(1 - t, 3);
    cible.textContent = formaterMontant(Math.round(totalTvac * adouci * 100) / 100);
    if (t < 1) requestAnimationFrame(etape);
  };
  requestAnimationFrame(etape);
}

function bloquerInterface(bloquer) {
  analyseEnCours = bloquer;
  champFichier.disabled = bloquer; // empêche d'ouvrir le sélecteur de fichier pendant l'analyse
  for (const bouton of document.querySelectorAll("button")) bouton.disabled = bloquer;
}

// --- Envoi au webhook n8n ---

async function analyser(fichier) {
  if (analyseEnCours) return;

  const estPdf = fichier.type === "application/pdf" || fichier.name.toLowerCase().endsWith(".pdf");
  if (!estPdf) {
    afficherErreur("Ce fichier n'est pas un PDF.");
    return;
  }
  if (fichier.size > TAILLE_MAX) {
    afficherErreur("Ce fichier dépasse 5 Mo.");
    return;
  }

  // Le nom "Document" est celui que le workflow n8n attend (champ Input Binary Field d'Extract from File).
  const donnees = new FormData();
  donnees.append("Document", fichier, fichier.name);

  bloquerInterface(true);
  afficherChargement(fichier.name);

  const annulation = new AbortController();
  const minuterie = setTimeout(() => annulation.abort(), DELAI_MAX);

  try {
    const reponse = await fetch(config.webhookUrl, {
      method: "POST",
      body: donnees,
      signal: annulation.signal,
    });
    const corps = await reponse.json().catch(() => null);

    // En cas de problème connu, le workflow renvoie { "erreur": "message pour le visiteur" }
    if (corps && corps.erreur) {
      afficherErreur(corps.erreur);
      return;
    }
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    if (!corps || !corps.output) throw new Error("Réponse sans champ output");
    afficherTermine(fichier.name);
    afficherResultat(corps.output);
  } catch (erreur) {
    console.error("Échec de l'analyse :", erreur);
    if (erreur.name === "AbortError") {
      afficherErreur("L'analyse a pris trop de temps. Le service d'IA est peut-être saturé.");
    } else {
      afficherErreur("L'analyse n'a pas pu aboutir.");
    }
  } finally {
    clearTimeout(minuterie);
    bloquerInterface(false);
    champFichier.value = "";
  }
}

async function analyserExemple(exemple, bouton) {
  if (analyseEnCours) return;
  const texteBouton = bouton.textContent;
  try {
    const reponse = await fetch(`exemples/${exemple.fichier}`);
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    const contenu = await reponse.blob();
    bouton.textContent = "Analyse...";
    await analyser(new File([contenu], exemple.fichier, { type: "application/pdf" }));
  } catch (erreur) {
    console.error("Impossible de charger l'exemple :", erreur);
    afficherErreur("Impossible de charger ce document d'exemple.");
  } finally {
    bouton.textContent = texteBouton;
  }
}

// --- Liste des exemples ---

for (const exemple of EXEMPLES) {
  const li = document.createElement("li");
  li.className = "exemple";

  const haut = document.createElement("div");
  haut.className = "exemple__haut";
  // Miniature de la première page (image générée à partir du document source)
  const apercu = document.createElement("img");
  apercu.className = "exemple__apercu";
  apercu.src = `exemples/apercus/${exemple.fichier.replace(".pdf", ".png")}`;
  apercu.alt = "";
  apercu.width = 56;
  apercu.height = 79;
  apercu.loading = "lazy";
  const infos = document.createElement("div");
  infos.className = "exemple__infos";
  const genre = document.createElement("span");
  genre.className = `exemple__genre ${exemple.type}`;
  genre.textContent = exemple.type === "devis" ? "Devis" : "Facture";
  const nom = document.createElement("div");
  nom.className = "exemple__nom";
  nom.textContent = exemple.nom;
  const numero = document.createElement("div");
  numero.className = "exemple__type";
  numero.textContent = exemple.numero;
  infos.append(genre, nom, numero);
  haut.append(apercu, infos);

  const actions = document.createElement("div");
  actions.className = "exemple__actions";
  const telecharger = document.createElement("a");
  telecharger.className = "bouton-lien";
  telecharger.href = `exemples/${exemple.fichier}`;
  telecharger.download = exemple.fichier;
  telecharger.textContent = "Télécharger";
  const essayer = document.createElement("button");
  essayer.type = "button";
  essayer.textContent = "Analyser";
  essayer.addEventListener("click", () => analyserExemple(exemple, essayer));
  actions.append(telecharger, essayer);

  li.append(haut, actions);
  listeExemples.append(li);
}

// --- Dépôt d'un fichier ---

afficherAttente();

// Lien permanent vers le classeur Excel public, en haut de la page
if (config.sheetUrl) {
  document.getElementById("tableur-direct-a").href = config.sheetUrl;
  document.getElementById("tableur-direct").hidden = false;
}

champFichier.addEventListener("change", () => {
  if (champFichier.files.length > 0) analyser(champFichier.files[0]);
});

// Toute la page accepte le glisser-déposer. Sans ça, Chrome ouvrirait le PDF à la place de la page.
// Le compteur évite que le voile clignote quand on passe d'un élément de la page à un autre.
let profondeurGlisser = 0;

function contientFichier(evenement) {
  return Array.from(evenement.dataTransfer?.types || []).includes("Files");
}

function cacherVoile() {
  profondeurGlisser = 0;
  voileDepot.classList.remove("visible");
  zoneDepot.classList.remove("survol");
}

window.addEventListener("dragenter", (evenement) => {
  if (!contientFichier(evenement)) return;
  evenement.preventDefault();
  if (analyseEnCours) return;
  profondeurGlisser += 1;
  voileDepot.classList.add("visible");
  zoneDepot.classList.add("survol");
});

window.addEventListener("dragover", (evenement) => {
  if (!contientFichier(evenement)) return;
  evenement.preventDefault();
  evenement.dataTransfer.dropEffect = analyseEnCours ? "none" : "copy";
});

window.addEventListener("dragleave", (evenement) => {
  if (!contientFichier(evenement)) return;
  profondeurGlisser -= 1;
  if (profondeurGlisser <= 0) cacherVoile();
});

window.addEventListener("drop", (evenement) => {
  if (!contientFichier(evenement)) return;
  evenement.preventDefault();
  cacherVoile();
  const fichier = evenement.dataTransfer.files[0];
  if (fichier) analyser(fichier);
});
