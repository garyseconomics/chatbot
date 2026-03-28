# Migration Plan — Moving to Gary's Server

This plan covers the steps needed to migrate the chatbot from the MakeSpace server
to a server owned by Gary's Economics.

## Current setup (MakeSpace Madrid)

- Docker containers run in a virtual machine on the MakeSpace AI server.
- The vector database (Chroma SQLite, ~28 MB) lives on the host filesystem, mounted
  into the containers via a Docker volume (`./data:/app/data`).
- The database is NOT inside the Docker image — it only exists on the server.

---

## Step 1. Set up a testing environment (free hosting)

Before setting up the production server, create a free VPS to test the full deployment
process. This lets us verify everything works without spending money.

**Free options:** Oracle Cloud Always Free or AWS t3.micro (12 months).

See [Phase 2 Plan, section 2.4](Phase_2_Plan.md#24-migrate-to-garys-server) for the
full comparison table.

Run through Steps 2–6 on the test server first. Once everything is verified, repeat on
the production server (Step 1b).

## Step 1b. Create the production account (paid hosting)

Once the test deployment is validated, create a paid VPS for production. No GPU needed —
the server only runs Docker containers, with chat and embeddings handled by cloud
providers.

**Budget:** ~$3–5/month.

**Top paid options:** Hetzner CX22 (~$3.60/mo, best value) or DigitalOcean ($6/mo,
$200 free credit for new accounts).

**RAM consideration:** The Chroma vector database is currently ~28 MB (~100 videos), but
will grow significantly as we add content (target 310+ videos plus potentially economist
documents). Providers with only 1 GB RAM (Vultr, AWS Lightsail, DigitalOcean basic) may
become tight as the database grows. Hetzner CX22 (4 GB) or Contabo (8 GB) give more
headroom.

See [Phase 2 Plan, section 2.4](Phase_2_Plan.md#24-migrate-to-garys-server) for the
full comparison table.

## Step 2. Create the VPS and set up Docker

- Create a VPS with Ubuntu.
- Basic security hardening: set up SSH key authentication, disable password login,
  configure firewall (UFW — allow SSH and outbound only). Discuss details with the team.
- Install Docker and Docker Compose.
- Clone the repository or copy `docker-compose.yml` and `.env` to the server.

## Step 3. Pull the Docker image

Pull the latest image from GHCR:

```bash
docker compose pull
```

The image is public at `ghcr.io/garyseconomics/chatbot:latest`.

## Step 4. Migrate the vector database

The Docker image only contains code and dependencies. The vector database must be
transferred separately.

1. Copy the `data/` folder from the old server to the new one:
   ```bash
   scp -r data/ newserver:/path/to/chatbot/data/
   ```
   The database is a single ~28 MB directory. A backup is also available at
   [garyseconomics/chatbot-database](https://github.com/garyseconomics/chatbot-database).

2. Add new subtitles on the new server using the import pipeline to verify the
   importer works in the new environment.

### Discarded options

**Separate Chroma container (client/server mode)** — Run Chroma as its own Docker
container with an HTTP API instead of reading the SQLite file directly. This is the
standard approach for larger deployments, but adds unnecessary complexity for our
~28 MB read-heavy database. Not worth it at this stage.

**Bake the database into the Docker image** — Include `data/` in the image so there's
nothing to transfer. But this would require rebuilding and re-deploying the image every
time we add new subtitles, which we expect to do regularly in Phase 2 (adding videos
after November 2025 and importing older transcripts).

## Step 5. Run tests

Run the test suite inside the Docker container to verify everything works:

```bash
docker compose run --rm telegram-bot pytest
```

## Step 6. Start the service and verify

**Important:** Stop the bots on the old server BEFORE starting them on the new one.
Running two instances of the same bot simultaneously will cause both to receive and
respond to messages unpredictably.

1. Stop the containers on the old server:
   ```bash
   docker compose down
   ```

2. Start the containers on the new server:
   ```bash
   docker compose up -d
   ```

3. Test with the CLI chatbot first to verify the RAG pipeline works.

4. Test with real messages on Telegram and Discord to confirm the bots are responding
   correctly through both platforms.

## Step 7. Transition period

Keep the MakeSpace server available (containers stopped but ready to restart) for a few
weeks after migration. If something goes wrong on the new server, we can quickly switch
back by stopping the new containers and restarting the old ones.
