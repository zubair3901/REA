// Stable public facade; feature implementations live in features/workspace.
import React from "react";
import "./workspace.css";
import { AccountGate } from "./features/workspace/AccountGate";
import Dashboard from "./features/workspace/ProjectDashboard";
export {
  WorkspaceProvider,
  useWorkspace,
} from "./features/workspace/WorkspaceContext";
export { Notice } from "./features/workspace/Notice";
export { AccountGate } from "./features/workspace/AccountGate";
export { Consultation } from "./features/workspace/Consultation";
export { Packages } from "./features/workspace/Packages";
export { Checkout } from "./features/workspace/Checkout";
export default function Workspace({ navigate, onDesign }) {
  return (
    <main className="rf-section">
      <AccountGate>
        <Dashboard navigate={navigate} onDesign={onDesign} />
      </AccountGate>
    </main>
  );
}
