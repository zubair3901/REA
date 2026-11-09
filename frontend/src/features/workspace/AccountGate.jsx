import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Plus,
  FolderOpen,
  Users,
  Check,
  LogOut,
  ArrowRight,
  Wallet,
  Package,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { api, API, money, label } from "../../workspace-api";
import { useWorkspace } from "./WorkspaceContext";
import { Notice } from "./Notice";
export function AccountGate({ children }) {
  const { user, ready, signedIn } = useWorkspace();
  const [mode, setMode] = useState(
      new URLSearchParams(location.search).has("reset")
        ? "reset-password"
        : "register",
    ),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  function changeMode(next) {
    setMode(next);
    setError("");
    setNotice("");
  }
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    const body = Object.fromEntries(new FormData(e.currentTarget));
    try {
      if (mode === "forgot-password") {
        const r = await api("/api/workspace/forgot-password", "POST", body);
        setNotice(r.message);
      } else if (mode === "reset-password") {
        await api("/api/workspace/reset-password", "POST", {
          password: body.password,
          token: new URLSearchParams(location.search).get("reset"),
        });
        window.location.assign("/?password_reset=1");
      } else {
        await signedIn(await api("/api/workspace/" + mode, "POST", body));
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  if (!ready)
    return (
      <p className="ws-notice" role="status">
        Opening your workspace…
      </p>
    );
  if (user && mode !== "reset-password") return children;
  return (
    <section className="ws-auth">
      <div className="ws-auth-story">
        <h2>
          A place for your
          <br />
          next project.
        </h2>
        <p>
          Create an account or sign in to save a project. Keep your room
          previews, budget, and order requests together.
        </p>
        <ul>
          <li>Projects that stay with you</li>
          <li>New and pre-loved furniture</li>
          <li>Local makers and skilled professionals</li>
        </ul>
        <small>Local product previews are free.</small>
      </div>
      <form onSubmit={submit} aria-busy={busy}>
        <h2>
          {mode === "register"
            ? "Create your account"
            : mode === "login"
              ? "Sign in to your projects"
              : mode === "forgot-password"
                ? "Reset your password"
                : "Choose a new password"}
        </h2>
        <div className="ws-tabs">
          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            aria-pressed={mode === "register"}
            disabled={busy}
            onClick={() => changeMode("register")}
          >
            Create account
          </button>
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            aria-pressed={mode === "login"}
            disabled={busy}
            onClick={() => changeMode("login")}
          >
            Sign in
          </button>
        </div>
        {mode === "register" && (
          <label>
            Your name
            <input
              name="name"
              minLength={2}
              maxLength={160}
              required
              autoComplete="name"
            />
          </label>
        )}
        {mode !== "reset-password" && (
          <label>
            Email
            <input
              name="email"
              type="email"
              required
              maxLength={254}
              autoComplete="email"
            />
          </label>
        )}
        {mode !== "forgot-password" && (
          <label>
            Password
            <input
              name="password"
              type="password"
              required
              minLength={12}
              maxLength={128}
              autoComplete={
                mode === "register" || mode === "reset-password"
                  ? "new-password"
                  : "current-password"
              }
            />
            <small>At least 12 characters</small>
          </label>
        )}
        <button className="rf-primary" disabled={busy}>
          {busy
            ? mode === "forgot-password"
              ? "Sending recovery link…"
              : mode === "reset-password"
                ? "Saving password…"
                : mode === "register"
                  ? "Creating account…"
                  : "Signing in…"
            : mode === "register"
              ? "Create my account"
              : mode === "login"
                ? "Sign in"
                : mode === "forgot-password"
                  ? "Send recovery link"
                  : "Save new password"}{" "}
          <ArrowRight size={16} />
        </button>
        <button
          type="button"
          className="rf-text-button"
          style={{ marginTop: 20 }}
          disabled={busy}
          onClick={() => changeMode("forgot-password")}
        >
          Forgot your password?
        </button>
        <Notice error>{error}</Notice>
        <Notice>{notice}</Notice>
      </form>
    </section>
  );
}
