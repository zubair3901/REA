import React, { useEffect, useState } from "react";
import { Package } from "lucide-react";
export default function SellerAuth({
  mode,
  setMode,
  busy,
  authenticate,
  manualKey,
  setManualKey,
  setToken,
  load,
}) {
  return (
    <main className="vendor-auth">
      <div>
        <span className="vendor-intro-icon">
          <Package size={32} />
        </span>
        <h1>
          Your products.
          <br />
          One organized workspace.
        </h1>
        <p>
          Manage furniture and decor inventory, keep stock accurate and receive
          clear delivery instructions from Roomform.
        </p>
        <ul>
          <li>Merchants and individual sellers welcome</li>
          <li>Your photographs, prices and availability</li>
          <li>Roomform coordinates the customer project</li>
        </ul>
      </div>
      <section className="vendor-auth-card">
        <h2>
          {mode === "login"
            ? "Sign in to your seller account"
            : "Create your seller account"}
        </h2>
        <div className="account-tabs">
          <button
            aria-pressed={mode === "login"}
            onClick={() => setMode("login")}
            type="button"
          >
            Sign in
          </button>
          <button
            aria-pressed={mode === "register"}
            onClick={() => setMode("register")}
            type="button"
          >
            Register as a seller
          </button>
        </div>
        <form onSubmit={authenticate}>
          {mode === "register" && (
            <>
              <label>
                Your name or shop name
                <input
                  name="name"
                  autoComplete="organization"
                  required
                  minLength={2}
                  maxLength={160}
                />
              </label>
              <label>
                Seller type
                <select name="kind">
                  <option value="merchant">Furniture or decor merchant</option>
                  <option value="individual">
                    Individual / pre-owned seller
                  </option>
                </select>
              </label>
            </>
          )}
          <label>
            Email address
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              required
              minLength={12}
            />
          </label>
          <button className="rf-primary" disabled={busy}>
            {busy
              ? "Opening your workspace…"
              : mode === "login"
                ? "Sign in to manage inventory"
                : "Create seller account"}
          </button>
        </form>
        <p>
          New accounts are reviewed before publishing. You can sign in to check
          your approval status.
        </p>
        <details className="manual-access">
          <summary>Existing merchant access</summary>
          <label>
            Merchant key or seller access token
            <input
              type="password"
              value={manualKey}
              onChange={(e) => setManualKey(e.target.value)}
              placeholder="Existing server-issued key"
            />
          </label>
          <button
            className="rf-text-button"
            onClick={() => {
              setToken(manualKey);
              load(manualKey);
            }}
          >
            Load my listings
          </button>
        </details>
      </section>
    </main>
  );
}
