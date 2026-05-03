# Manual QA Checklist

Use this before recording a demo, taking screenshots, or pushing a release.

## 1. Backend Startup

- Run `.\scripts\start_backend.ps1`.
- Confirm the terminal prints `http://127.0.0.1:8010`.
- Open `http://127.0.0.1:8010/health`.
- Expected: `{"status":"ok"}`.
- Opening `http://127.0.0.1:8010` may show `Not Found`; that is normal.

## 2. Frontend Startup

- Run `.\scripts\start_frontend.ps1` in a second terminal.
- Open `http://localhost:3000`.
- If port 3000 is busy, use the port printed by Next.js, usually 3001.

## 3. Settings Check

- Open Settings.
- Confirm provider, model, key configured yes/no, fallback, embedding provider, RAG mode, strict citation mode.
- Confirm no raw API key is visible.

## 4. Test Provider Check

- In mock mode, click `Test Provider`; expected success without external API call.
- In Gemini mode, click `Test Provider`; expected success or fallback/error with a clear message.
- Confirm no secret appears in the UI.

## 5. Mock Chat Check

- Set `LLM_PROVIDER=mock`.
- Ask `What can AgentOS Lite do?`
- Expected intent: project overview style answer.
- Confirm no RAG citations are invented for general overview.

## 6. Gemini Chat Check

- Set `LLM_PROVIDER=gemini`, configure key locally, restart backend.
- Ask a simple question in Chat.
- Confirm LLMOps shows provider/model/latency/status.
- If fallback happens, confirm LLMOps shows fallback reason.

## 7. Documents / RAG Check

- Upload or load `examples/sample_docs/product_brief.md`.
- View chunk preview.
- Ask `Summarize the uploaded product brief.`
- Expected: answer references retrieved content and citation cards show document name, chunk label, snippet, matched/debug info, and score.
- Delete and reindex actions should complete without UI breakage.

## 8. Memory Check

- Add a memory: `I prefer concise technical explanations with practical examples.`
- Ask `How should you explain technical topics to me?`
- Expected: answer uses the actual memory content naturally.

## 9. Codebase Check

- Click `Index AgentOS Lite repo`.
- Confirm repo map appears.
- Ask `Explain the architecture of this repo.`
- Ask `Where is Gemini provider implemented?`
- Ask `Generate test suggestions for Gemini provider.`
- Expected: module summary, target files, why matched, citations, and test sections.

## 10. Tools / Approvals Check

- Trigger a memory-save or report-generation action from Chat.
- Confirm approval-required state appears.
- Open Tools.
- Approve one request and reject another if available.
- Confirm tool call history updates.
- Confirm blocked tool stays blocked if tested by backend tests.

## 11. LLMOps Check

- Open LLMOps.
- Confirm summary cards show runs, calls, retrievals, tools, errors, provider, fallback count.
- Expand a run/raw JSON only when needed.
- Confirm no raw API key appears.

## 12. No-Secret Check

- `.env` is ignored by Git.
- `backend/.env` is not staged.
- Settings shows key configured yes/no only.
- LLMOps does not store or display key.
- Codebase indexing ignores `.env`, databases, logs, node_modules, `.git`, `.next`, build/dist/cache.

## 13. GitHub Pre-Commit Check

Run:

```powershell
git status --short
git diff --check
git diff
```

Expected: no real key and no `.env` staged. Manually inspect the diff for Gemini key-looking strings and local private Windows user paths before committing.

Run validation:

```powershell
$env:PYTHONPATH="backend"
pytest backend\app\tests
python -c "from app.main import app; print(app.title)"
cd frontend
npm run typecheck
npm run build
```

## 14. Local Mock QA

- `APP_ENV=local`
- `LLM_PROVIDER=mock`
- `DEMO_MODE=false`
- Confirm Chat, Documents, Memory, Codebase, Tools, and LLMOps work without API keys.

## 15. Local Gemini QA

- `APP_ENV=local`
- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY` set only in local `backend/.env`
- `DEMO_MODE=false`
- Confirm Settings `Test Provider` works or falls back clearly.
- Confirm LLMOps does not show the key.

## 16. Hosted Demo QA

- Vercel `NEXT_PUBLIC_API_BASE_URL` points to Render backend.
- Render backend env has `APP_ENV=production`, `LLM_PROVIDER=gemini`, `DEMO_MODE=true`, `MAX_LLM_CALLS_PER_USER_PER_DAY=5`, `DEMO_FALLBACK_TO_MOCK=true`.
- `CORS_ORIGINS` includes the Vercel domain.
- Settings shows Hosted demo and remaining calls.
- Chat requests preserve the anonymous cookie.

## 17. Rate Limit QA

- In a mocked or disposable environment, set `MAX_LLM_CALLS_PER_USER_PER_DAY=1`.
- First Gemini call should use provider `gemini`.
- Second call should use provider `mock`, attempted provider `gemini`, and `fallback_reason=demo_daily_limit`.
- Chat should show the daily limit fallback notice.

## 18. Hosted No-Secret QA

- Render env contains the real Gemini key, Git does not.
- Vercel env contains only `NEXT_PUBLIC_API_BASE_URL`.
- README/docs use empty Gemini API key placeholders.
- LLMOps shows provider/model/fallback, never secret values.
