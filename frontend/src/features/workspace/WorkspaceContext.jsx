import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../../workspace-api";
const Context = createContext(null);
export const useWorkspace = () => useContext(Context);
export function WorkspaceProvider({ children }) {
  const [user, setUser] = useState(null),
    [ready, setReady] = useState(false),
    [projects, setProjects] = useState([]),
    [activeId, setActiveId] = useState(
      sessionStorage.getItem("roomform-project") || "",
    );
  async function refresh() {
    const p = await api("/api/workspace/projects");
    setProjects(p);
    return p;
  }
  useEffect(() => {
    api("/api/workspace/me")
      .then(async (u) => {
        setUser(u);
        await refresh();
      })
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);
  function select(id) {
    setActiveId(id);
    sessionStorage.setItem("roomform-project", id);
  }
  async function signedIn(u) {
    setUser(u);
    await refresh();
  }
  async function logout() {
    await api("/api/workspace/logout", "POST");
    setUser(null);
    setProjects([]);
    select("");
  }
  return (
    <Context.Provider
      value={{
        user,
        ready,
        projects,
        activeId,
        active: projects.find((p) => p.id === activeId),
        select,
        refresh,
        signedIn,
        logout,
      }}
    >
      {children}
    </Context.Provider>
  );
}
