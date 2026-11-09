import React from "react";
import { createRoot } from "react-dom/client";
import { WorkspaceProvider } from "./Workspace";
import App from "./app/App";

createRoot(document.getElementById("root")).render(
  <WorkspaceProvider>
    <App />
  </WorkspaceProvider>,
);
