# Deploy Instructions — GitHub Pages

## Step 1: Commit the docs/ folder

```bash
cd C:\Users\Kico\PycharmProjects\MusicByKico

git add docs/
git commit -m "docs: add Privacy Policy, Terms of Service, and legal pages"
git push origin main
```

> If your default branch is `dev` or `master`, replace `main` accordingly.

---

## Step 2: Enable GitHub Pages

1. Go to: **https://github.com/Oleksii1221/MusicByKico**
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Source**, select:
   - Branch: `main` (or whichever branch you pushed to)
   - Folder: `/docs`
4. Click **Save**
5. Wait ~1 minute. GitHub will show the published URL.

---

## Step 3: Your URLs

```
https://oleksii1221.github.io/MusicByKico/
https://oleksii1221.github.io/MusicByKico/privacy.html
https://oleksii1221.github.io/MusicByKico/terms.html
```

---

## Step 4: Add to Discord Developer Portal

1. Go to: **https://discord.com/developers/applications**
2. Select **MusicByKico**
3. Click **General Information**
4. Fill in:
   - **Privacy Policy URL** → `https://oleksii1221.github.io/MusicByKico/privacy.html`
   - **Terms of Service URL** → `https://oleksii1221.github.io/MusicByKico/terms.html`
5. Click **Save Changes**

---

## Notes

- GitHub Pages is free for public repositories.
- If your repository is private, you need GitHub Pro for Pages.
- If you update the bot's data handling, update `privacy.html` section 5 and bump the "Last updated" date.
