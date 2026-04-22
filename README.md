# GNM — Glen's Note Management

Automated pipeline: Inq Smart Pen + Otter.ai transcripts -> Claude AI processing -> structured Obsidian vault -> queryable dashboard.

## Quick Start

```bash
git clone https://github.com/danvelarde/GNM.git
cd GNM
python setup_vault.py
```

The setup script will ask for:
- **Vault path** — where to create the Obsidian vault
- **Inbox path** — where raw notes/transcripts are dropped (Dropbox)
- **Projects** — initial project folders to create

It then generates the full folder structure, Obsidian config, Dataview plugin setup, and starter templates.

## Vault Structure

```
GlenVault/
  Projects/
    <ProjectName>/
      Notes/
      Transcripts/
      AI Analyzed Notes/YYYY/WNN_MonDD-MonDD/
      Action Items/YYYY/WNN_MonDD-MonDD/
      Weekly Reports/YYYY/
      People/
  Attachments/
  Templates/
```

## Inbox Structure

```
NoteInbox/
  Inq/        <- Raw Inq pen exports
  Otter/      <- Raw Otter.ai transcripts
  Manual/     <- Ad-hoc notes dropped manually
  Processed/  <- Files moved here after processing
```
