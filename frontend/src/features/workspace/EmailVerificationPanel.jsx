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
export function EmailVerificationPanel() {
  const [message, setMessage] = useState("");
  return (
    <details className="ws-card">
      <summary>Verify your email</summary>
      <p>Verify your email before making requests on secure staging.</p>
      <button
        className="rf-text-button"
        onClick={async () => {
          try {
            await api("/api/workspace/verification/send", "POST");
            setMessage("Check your email for your verification token.");
          } catch (e) {
            setMessage(e.message);
          }
        }}
      >
        Send verification email
      </button>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const token = new FormData(e.currentTarget).get("token");
          try {
            await api("/api/workspace/verification/confirm", "POST", { token });
            setMessage("Your email is verified.");
          } catch (e) {
            setMessage(e.message);
          }
        }}
      >
        <label>
          Token from email
          <input name="token" required minLength={30} />
        </label>
        <button className="rf-primary">Verify email</button>
      </form>
      <Notice>{message}</Notice>
    </details>
  );
}
