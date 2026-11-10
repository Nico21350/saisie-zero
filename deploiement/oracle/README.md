# Serveur n8n (Oracle Cloud Always Free)

Fichiers copiés dans `/opt/saisie-zero/` sur le serveur, avec un fichier `.env` (modèle : `.env.example`) dont les valeurs sont générées sur le serveur et n'en sortent pas.

- `docker-compose.yml` : PostgreSQL, n8n et Caddy.
- `Caddyfile` : Caddy obtient le certificat HTTPS et ne transmet à n8n **que** l'adresse du webhook `/webhook/saisie-zero`. Tout le reste (éditeur, API) répond 404.

## Ouvrir l'éditeur n8n

L'éditeur n'est pas accessible depuis Internet. On l'ouvre par un tunnel SSH, qui relie un port de son PC au port 5678 du serveur.

1. Dans un terminal (PowerShell) :

   ```
   ssh -i $HOME\.ssh\oracle_saisie_zero -N -L 5680:127.0.0.1:5678 ubuntu@<adresse-du-serveur>
   ```

   La commande ne rend pas la main : c'est normal, le tunnel reste ouvert tant que la fenêtre l'est.
2. Dans le navigateur : `http://localhost:5680`, puis se connecter avec le compte n8n.
3. Pour fermer le tunnel : `Ctrl + C` dans le terminal.

Le port 5680 évite le conflit avec un n8n local, qui utilise déjà le 5678.

## Refaire une connexion Microsoft ou Google (OAuth)

La page de retour d'OAuth (`/rest/oauth2-credential/callback`) passe par l'adresse publique, fermée par Caddy. Pour reconnecter un identifiant : remettre temporairement `reverse_proxy n8n:5678` pour tout le site dans le `Caddyfile`, recharger Caddy, faire la connexion sur l'adresse publique, puis remettre la version fermée.

```
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```
