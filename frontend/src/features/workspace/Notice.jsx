import React from "react";
export function Notice({ children, error = false }) {
  return children ? (
    <div
      className={"ws-notice " + (error ? "error" : "")}
      role={error ? "alert" : "status"}
    >
      {children}
    </div>
  ) : null;
}
