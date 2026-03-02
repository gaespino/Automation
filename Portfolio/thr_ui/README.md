# THR Tools — Frontend (React + TypeScript + Vite)

This is the React/TypeScript frontend for the THR Tools Portfolio application. The FastAPI backend (`../app.py`) serves the compiled output from `dist/` as static files, so **Node.js is only required when you change source files** — not at runtime.

---

## Why `dist/` is committed to git

The root `.gitignore` excludes `dist/` globally (a standard Python packaging rule), but contains explicit negation overrides so this folder **is** tracked:

```
# React build output — committed so users don't need Node.js to run the app
!Portfolio/thr_ui/dist/
!Portfolio/thr_ui/dist/**
```

This means:
- The server can serve the UI straight after `git pull` — no build step needed to *run* the app.
- After making source changes (`src/**/*.tsx`, `src/**/*.ts`, etc.) you **must** rebuild `dist/` and commit it so others see the updated UI.

---

## Rebuilding `dist/` after source changes

Every time you edit a source file you must regenerate the compiled output:

```bash
cd Portfolio/thr_ui

# Install dependencies (first time only, or after package.json changes)
npm install

# Rebuild — output goes to dist/
npm run build
```

Then commit the changed `dist/` files along with your source changes:

```bash
git add src/...          # your source edits
git add dist/            # the rebuilt output
git commit -m "Your change description"
```

> **Important:** If you push source changes without rebuilding `dist/`, the running application will still show the old UI because the server serves `dist/` directly.

---

## Development workflow (live-reload)

For iterative development you can run the Vite dev server, which hot-reloads on every save — **no manual rebuild needed**:

```bash
cd Portfolio/thr_ui
npm install        # first time only
npm run dev        # starts on http://localhost:5173
```

The dev server proxies API calls to the FastAPI backend. Start the backend first:

```bash
cd Portfolio
pip install -r requirements.txt   # first time only
python app.py                      # starts on http://localhost:8000
```

When you are happy with your changes, run `npm run build` to update `dist/` and commit everything.

---

## Available scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with hot-reload (port 5173) |
| `npm run build` | Compile source → `dist/` (required before committing UI changes) |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint on source files |
