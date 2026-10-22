
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const initialFeatures = {
  limit_bal: 50000,
  pay_status_sep: 0,
  pay_status_aug: 0,
  pay_status_jul: 0,
  pay_status_jun: 0,
  pay_status_may: 0,
  pay_status_apr: 0,
  bill_amt1: 20000,
  bill_amt2: 18000,
  bill_amt3: 16000,
  bill_amt4: 14000,
  bill_amt5: 12000,
  bill_amt6: 10000,
  pay_amt1: 3000,
  pay_amt2: 3000,
  pay_amt3: 3000,
  pay_amt4: 3000,
  pay_amt5: 3000,
  pay_amt6: 3000,
};

const featureLabels = {
  limit_bal: "Credit limit",
  pay_status_sep: "September repayment status",
  pay_status_aug: "August repayment status",
  pay_status_jul: "July repayment status",
  pay_status_jun: "June repayment status",
  pay_status_may: "May repayment status",
  pay_status_apr: "April repayment status",
  bill_amt1: "September bill amount",
  bill_amt2: "August bill amount",
  bill_amt3: "July bill amount",
  bill_amt4: "June bill amount",
  bill_amt5: "May bill amount",
  bill_amt6: "April bill amount",
  pay_amt1: "September payment amount",
  pay_amt2: "August payment amount",
  pay_amt3: "July payment amount",
  pay_amt4: "June payment amount",
  pay_amt5: "May payment amount",
  pay_amt6: "April payment amount",
};

const repaymentOptions = [
  { value: -2, label: "-2 — No consumption" },
  { value: -1, label: "-1 — Paid duly" },
  { value: 0, label: "0 — Revolving credit" },
  { value: 1, label: "1 — 1 month delay" },
  { value: 2, label: "2 — 2 months delay" },
  { value: 3, label: "3 — 3 months delay" },
  { value: 4, label: "4 — 4 months delay" },
  { value: 5, label: "5 — 5 months delay" },
  { value: 6, label: "6 — 6 months delay" },
  { value: 7, label: "7 — 7 months delay" },
  { value: 8, label: "8 — 8+ months delay" },
];

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
}

function formatMoney(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function getBorrowerId(borrower) {
  return borrower?.borrower_id ?? borrower?.id;
}

function getRiskClass(category) {
  const value = String(category || "").toLowerCase();
  if (value.includes("low") || value.includes("lower")) return "low";
  if (value.includes("moderate") || value.includes("medium")) return "moderate";
  return "high";
}

function getErrorMessage(data, fallback) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || "Invalid input").join(", ");
  }
  return data?.message || fallback;
}

export default function Home() {
  const [activeView, setActiveView] = useState("Overview");
  const [borrowers, setBorrowers] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [selectedBorrowerId, setSelectedBorrowerId] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingBorrower, setSavingBorrower] = useState(false);
  const [runningAssessment, setRunningAssessment] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [backendStatus, setBackendStatus] = useState("Checking");
  const [searchTerm, setSearchTerm] = useState("");
  const [borrowerName, setBorrowerName] = useState("");
  const [externalReference, setExternalReference] = useState("");
  const [features, setFeatures] = useState(initialFeatures);
  const [latestResult, setLatestResult] = useState(null);

  const selectedBorrower = borrowers.find(
    (borrower) => String(getBorrowerId(borrower)) === String(selectedBorrowerId)
  );

  const request = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        getErrorMessage(data, `Request failed (${response.status})`)
      );
    }

    return data;
  }, []);

  const loadBorrowers = useCallback(async () => {
    const data = await request("/borrowers");
    const list = Array.isArray(data) ? data : data?.borrowers || [];
    setBorrowers(list);

    setSelectedBorrowerId((currentId) => {
      const currentStillExists = list.some(
        (borrower) => String(getBorrowerId(borrower)) === String(currentId)
      );
      if (currentStillExists) return currentId;
      return list.length ? String(getBorrowerId(list[0])) : "";
    });

    return list;
  }, [request]);

  const loadAssessments = useCallback(
    async (borrowerId) => {
      if (!borrowerId) {
        setAssessments([]);
        return [];
      }

      const data = await request(`/borrowers/${borrowerId}/assessments`);
      const list = Array.isArray(data)
        ? data
        : data?.assessments || [];

      const sorted = [...list].sort(
        (a, b) =>
          new Date(b.assessed_at || 0).getTime() -
          new Date(a.assessed_at || 0).getTime()
      );

      setAssessments(sorted);
      if (sorted.length) setLatestResult(sorted[0]);
      return sorted;
    },
    [request]
  );

  useEffect(() => {
    let cancelled = false;

    async function initialise() {
      setLoading(true);
      setError("");

      try {
        await request("/health/db");
        if (!cancelled) setBackendStatus("Connected");
      } catch {
        if (!cancelled) setBackendStatus("Offline");
      }

      try {
        const data = await request("/borrowers");
        if (cancelled) return;

        const list = Array.isArray(data) ? data : data?.borrowers || [];
        setBorrowers(list);
        setSelectedBorrowerId(
          list.length ? String(getBorrowerId(list[0])) : ""
        );
      } catch (err) {
        if (!cancelled) {
          setError(
            `${err.message}. Check that FastAPI is running at ${API_URL}.`
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    initialise();
    return () => {
      cancelled = true;
    };
  }, [request]);

  useEffect(() => {
    if (!selectedBorrowerId) {
      setAssessments([]);
      return;
    }

    let cancelled = false;

    request(`/borrowers/${selectedBorrowerId}/assessments`)
      .then((data) => {
        if (cancelled) return;
        const list = Array.isArray(data) ? data : data?.assessments || [];
        const sorted = [...list].sort(
          (a, b) =>
            new Date(b.assessed_at || 0).getTime() -
            new Date(a.assessed_at || 0).getTime()
        );
        setAssessments(sorted);
        if (sorted.length) setLatestResult(sorted[0]);
      })
      .catch(() => {
        if (!cancelled) setAssessments([]);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedBorrowerId, request]);

  const allAssessments = useMemo(() => assessments, [assessments]);

  const latestAssessment = latestResult || allAssessments[0] || null;

  const filteredBorrowers = borrowers.filter((borrower) => {
    const name = String(borrower.full_name || "").toLowerCase();
    const reference = String(borrower.external_reference || "").toLowerCase();
    const term = searchTerm.toLowerCase();
    return name.includes(term) || reference.includes(term);
  });

  const highRiskCount = allAssessments.filter((item) =>
    getRiskClass(item.risk_category).includes("high")
  ).length;

  async function handleAddBorrower(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!borrowerName.trim()) {
      setError("Enter the borrower's full name.");
      return;
    }

    setSavingBorrower(true);

    try {
      const created = await request("/borrowers", {
        method: "POST",
        body: JSON.stringify({
          full_name: borrowerName.trim(),
          managed_by: 1,
          external_reference: externalReference.trim() || null,
        }),
      });

      const newId = getBorrowerId(created);
      const list = await loadBorrowers();

      if (newId !== undefined && newId !== null) {
        setSelectedBorrowerId(String(newId));
      } else if (list.length) {
        const matching = list.find(
          (item) => item.full_name === borrowerName.trim()
        );
        if (matching) setSelectedBorrowerId(String(getBorrowerId(matching)));
      }

      setBorrowerName("");
      setExternalReference("");
      setSuccess("Borrower added successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingBorrower(false);
    }
  }

  async function handleAssessment(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLatestResult(null);

    if (!selectedBorrowerId) {
      setError("Add or select a borrower before running an assessment.");
      return;
    }

    setRunningAssessment(true);

    try {
      const payload = Object.fromEntries(
        Object.entries(features).map(([key, value]) => [key, Number(value)])
      );

      const result = await request(
        `/borrowers/${selectedBorrowerId}/assess`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      setLatestResult(result);
      setSuccess("Risk assessment completed successfully.");
      await loadAssessmentsForCurrentBorrower();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunningAssessment(false);
    }
  }

  async function loadAssessmentsForCurrentBorrower() {
    if (!selectedBorrowerId) return;

    try {
      const data = await request(
        `/borrowers/${selectedBorrowerId}/assessments`
      );
      const list = Array.isArray(data) ? data : data?.assessments || [];
      const sorted = [...list].sort(
        (a, b) =>
          new Date(b.assessed_at || 0).getTime() -
          new Date(a.assessed_at || 0).getTime()
      );
      setAssessments(sorted);
    } catch {
      // Keep the assessment result visible even if history refresh fails.
    }
  }

  function updateFeature(key, value) {
    setFeatures((current) => ({ ...current, [key]: value }));
  }

  function renderRiskBadge(category) {
    const riskClass = getRiskClass(category);
    return (
      <span className={`risk-badge ${riskClass}`}>
        <span className="badge-dot" />
        {category || "Unknown"}
      </span>
    );
  }

  function renderAssessmentResult(result) {
    if (!result) {
      return (
        <div className="empty-state">
          <h3>No assessment result yet</h3>
          <p>Select a borrower and run a risk assessment to see the prediction.</p>
        </div>
      );
    }

    const probability = Number(result.default_probability);
    const score = result.risk_score;

    return (
      <div className="result-panel">
        <div className="result-heading">
          <div>
            <h3>Assessment result</h3>
            <p className="panel-description">
              {selectedBorrower?.full_name || "Selected borrower"}
            </p>
          </div>
          {renderRiskBadge(result.risk_category)}
        </div>

        <div className="result-grid">
          <div className="result-item">
            <span className="result-item-label">Risk score</span>
            <strong className="result-item-value">
              {score !== undefined && score !== null ? `${score}/100` : "—"}
            </strong>
          </div>
          <div className="result-item">
            <span className="result-item-label">Default probability</span>
            <strong className="result-item-value">
              {Number.isFinite(probability)
                ? `${(probability * 100).toFixed(1)}%`
                : "—"}
            </strong>
          </div>
          <div className="result-item">
            <span className="result-item-label">Model</span>
            <strong className="result-item-value">
              {result.model_name || "Credit risk model"}
            </strong>
          </div>
          <div className="result-item">
            <span className="result-item-label">Assessed on</span>
            <strong className="result-item-value">
              {formatDate(result.assessed_at)}
            </strong>
          </div>
        </div>

        <p className="result-disclaimer">
          This is an experimental prediction, not a lending decision. The model
          was trained on a historical Taiwan credit-card dataset and has not
          been validated for Indian borrowers. Its probability output may not
          be calibrated.
        </p>
      </div>
    );
  }

  function renderOverview() {
    return (
      <>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-top">
              <span>Total borrowers</span>
              <span className="metric-icon blue">♙</span>
            </div>
            <div className="metric-value">{borrowers.length}</div>
            <div className="metric-detail">Borrowers in the database</div>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>Selected borrower</span>
              <span className="metric-icon purple">◎</span>
            </div>
            <div className="metric-value">
              {selectedBorrower ? `#${getBorrowerId(selectedBorrower)}` : "—"}
            </div>
            <div className="metric-detail">
              {selectedBorrower?.full_name || "No borrower selected"}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>Latest risk score</span>
              <span className="metric-icon amber">↗</span>
            </div>
            <div className="metric-value">
              {latestAssessment?.risk_score ?? "—"}
            </div>
            <div className="metric-detail">
              {latestAssessment?.risk_category || "Run an assessment to begin"}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-top">
              <span>High-risk assessments</span>
              <span className="metric-icon red">!</span>
            </div>
            <div className="metric-value">{highRiskCount}</div>
            <div className="metric-detail">
              In the selected borrower's history
            </div>
          </div>
        </div>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Borrowers</h2>
              <p className="panel-description">
                View records and choose a borrower for risk assessment.
              </p>
            </div>
            <button
              className="button button-primary"
              onClick={() => setActiveView("Borrowers")}
            >
              + Add borrower
            </button>
          </div>

          {renderBorrowerTable(borrowers.slice(0, 5))}
          {borrowers.length > 5 && (
            <div className="form-actions">
              <button
                className="button button-secondary"
                onClick={() => setActiveView("Borrowers")}
              >
                View all borrowers
              </button>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Latest assessment</h2>
              <p className="panel-description">
                Most recent result for the selected borrower.
              </p>
            </div>
            <button
              className="button button-secondary"
              onClick={() => setActiveView("Risk assessment")}
            >
              Run assessment
            </button>
          </div>
          {renderAssessmentResult(latestAssessment)}
        </section>
      </>
    );
  }

  function renderBorrowerTable(list) {
    if (loading) {
      return <div className="loading-state">Loading borrowers…</div>;
    }

    if (!list.length) {
      return (
        <div className="empty-state">
          <h3>No borrowers found</h3>
          <p>Add a borrower using the form to get started.</p>
        </div>
      );
    }

    return (
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Borrower</th>
              <th>Reference</th>
              <th>Created</th>
              <th>Latest risk</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {list.map((borrower) => {
              const id = getBorrowerId(borrower);
              const isSelected = String(id) === String(selectedBorrowerId);

              return (
                <tr key={id} className={isSelected ? "selected-row" : ""}>
                  <td>
                    <div className="borrower-name">
                      {borrower.full_name || "Unnamed borrower"}
                    </div>
                    <div className="borrower-subtitle">ID: {id}</div>
                  </td>
                  <td>{borrower.external_reference || "—"}</td>
                  <td>{formatDate(borrower.created_at)}</td>
                  <td>
                    {isSelected && latestAssessment
                      ? renderRiskBadge(latestAssessment.risk_category)
                      : "—"}
                  </td>
                  <td>
                    <button
                      className="table-action"
                      onClick={() => {
                        setSelectedBorrowerId(String(id));
                        setActiveView("Risk assessment");
                      }}
                    >
                      Select
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }

  function renderBorrowers() {
    return (
      <>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Add a borrower</h2>
              <p className="panel-description">
                Create a borrower record in PostgreSQL.
              </p>
            </div>
          </div>

          <form onSubmit={handleAddBorrower}>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="borrower-name">Full name *</label>
                <input
                  id="borrower-name"
                  value={borrowerName}
                  onChange={(event) => setBorrowerName(event.target.value)}
                  placeholder="Enter full name"
                  required
                />
              </div>
              <div className="form-field">
                <label htmlFor="borrower-reference">External reference</label>
                <input
                  id="borrower-reference"
                  value={externalReference}
                  onChange={(event) =>
                    setExternalReference(event.target.value)
                  }
                  placeholder="Optional customer reference"
                />
              </div>
            </div>
            <div className="form-actions">
              <button
                className="button button-primary"
                type="submit"
                disabled={savingBorrower}
              >
                {savingBorrower ? "Saving…" : "Create borrower"}
              </button>
            </div>
          </form>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">All borrowers</h2>
              <p className="panel-description">
                Select a record to assess its credit risk.
              </p>
            </div>
          </div>

          <div className="toolbar">
            <div className="search-box">
              <span>⌕</span>
              <input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search name or reference…"
              />
            </div>
            <span className="record-count">
              {filteredBorrowers.length} records
            </span>
          </div>

          {renderBorrowerTable(filteredBorrowers)}
        </section>
      </>
    );
  }

  function renderAssessmentForm() {
    const statusKeys = [
      "pay_status_sep",
      "pay_status_aug",
      "pay_status_jul",
      "pay_status_jun",
      "pay_status_may",
      "pay_status_apr",
    ];

    const moneyKeys = [
      "limit_bal",
      "bill_amt1",
      "bill_amt2",
      "bill_amt3",
      "bill_amt4",
      "bill_amt5",
      "bill_amt6",
      "pay_amt1",
      "pay_amt2",
      "pay_amt3",
      "pay_amt4",
      "pay_amt5",
      "pay_amt6",
    ];

    return (
      <>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Choose a borrower</h2>
              <p className="panel-description">
                The assessment will be saved against the selected borrower.
              </p>
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="assessment-borrower">Borrower</label>
            <select
              id="assessment-borrower"
              value={selectedBorrowerId}
              onChange={(event) => setSelectedBorrowerId(event.target.value)}
            >
              <option value="">Select a borrower</option>
              {borrowers.map((borrower) => (
                <option
                  key={getBorrowerId(borrower)}
                  value={String(getBorrowerId(borrower))}
                >
                  {borrower.full_name} (ID: {getBorrowerId(borrower)})
                </option>
              ))}
            </select>
          </div>
        </section>

        <form onSubmit={handleAssessment}>
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Credit profile</h2>
                <p className="panel-description">
                  Enter the credit limit, repayment status, bills, and payments.
                </p>
              </div>
            </div>

            <div className="feature-group">
              <h3>Credit limit</h3>
              <div className="feature-grid">
                {moneyKeys.slice(0, 1).map((key) => (
                  <div className="feature-field" key={key}>
                    <label htmlFor={key}>{featureLabels[key]}</label>
                    <input
                      id={key}
                      type="number"
                      min="0"
                      step="any"
                      value={features[key]}
                      onChange={(event) => updateFeature(key, event.target.value)}
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="feature-group">
              <h3>Repayment status</h3>
              <p className="panel-description">
                Use the status recorded for each month in the dataset.
              </p>
              <div className="feature-grid">
                {statusKeys.map((key) => (
                  <div className="feature-field" key={key}>
                    <label htmlFor={key}>{featureLabels[key]}</label>
                    <select
                      id={key}
                      value={features[key]}
                      onChange={(event) => updateFeature(key, event.target.value)}
                      required
                    >
                      {repaymentOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            <div className="feature-group">
              <h3>Bill amounts</h3>
              <div className="feature-grid">
                {moneyKeys.slice(1, 7).map((key) => (
                  <div className="feature-field" key={key}>
                    <label htmlFor={key}>{featureLabels[key]}</label>
                    <input
                      id={key}
                      type="number"
                      step="any"
                      value={features[key]}
                      onChange={(event) => updateFeature(key, event.target.value)}
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="feature-group">
              <h3>Payment amounts</h3>
              <div className="feature-grid">
                {moneyKeys.slice(7).map((key) => (
                  <div className="feature-field" key={key}>
                    <label htmlFor={key}>{featureLabels[key]}</label>
                    <input
                      id={key}
                      type="number"
                      min="0"
                      step="any"
                      value={features[key]}
                      onChange={(event) => updateFeature(key, event.target.value)}
                      required
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="form-actions">
              <button
                className="button button-primary"
                type="submit"
                disabled={runningAssessment || !selectedBorrowerId}
              >
                {runningAssessment
                  ? "Assessing…"
                  : "Run credit risk assessment"}
              </button>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => setFeatures(initialFeatures)}
              >
                Reset values
              </button>
            </div>
          </section>
        </form>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Prediction</h2>
              <p className="panel-description">
                The latest model output for the selected borrower.
              </p>
            </div>
          </div>
          {renderAssessmentResult(latestResult)}
        </section>
      </>
    );
  }

  function renderHistory() {
    return (
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Assessment history</h2>
            <p className="panel-description">
              Saved risk assessments for the currently selected borrower.
            </p>
          </div>
          <div className="panel-actions">
            <select
              aria-label="Select borrower for assessment history"
              value={selectedBorrowerId}
              onChange={(event) => setSelectedBorrowerId(event.target.value)}
            >
              <option value="">Select borrower</option>
              {borrowers.map((borrower) => (
                <option
                  key={getBorrowerId(borrower)}
                  value={String(getBorrowerId(borrower))}
                >
                  {borrower.full_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {!allAssessments.length ? (
          <div className="empty-state">
            <h3>No assessment history</h3>
            <p>Run an assessment to create the first history record.</p>
          </div>
        ) : (
          <div className="history-list">
            {allAssessments.map((item, index) => (
              <div
                className="history-item"
                key={item.assessment_id ?? item.id ?? index}
              >
                <div>
                  <div className="history-meta">
                    {formatDate(item.assessed_at)} · Assessment #
                    {item.assessment_id ?? item.id ?? index + 1}
                  </div>
                  <div>{renderRiskBadge(item.risk_category)}</div>
                  <div className="borrower-subtitle">
                    Model: {item.model_name || "Credit risk model"}
                  </div>
                </div>
                <div className="history-score">
                  {item.risk_score ?? "—"}/100
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    );
  }

  const navigation = [
    { label: "Overview", icon: "⌂" },
    { label: "Borrowers", icon: "♙" },
    { label: "Risk assessment", icon: "◈" },
    { label: "Assessment history", icon: "◷" },
  ];

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">CR</div>
          <div>
            <div className="brand-name">Credence</div>
            <div className="brand-subtitle">Credit Risk Platform</div>
          </div>
        </div>

        <div className="nav-heading">WORKSPACE</div>
        <nav className="nav-links">
          {navigation.map((item) => (
            <button
              key={item.label}
              className={`nav-link ${
                activeView === item.label ? "active" : ""
              }`}
              onClick={() => setActiveView(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span
            className={`connection-dot ${
              backendStatus !== "Connected" ? "offline" : ""
            }`}
          />
          <span>
            Backend: {backendStatus === "Checking" ? "Checking…" : backendStatus}
          </span>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <div className="eyebrow">CREDIT RISK MANAGEMENT</div>
            <h1 className="page-title">{activeView}</h1>
            <p className="page-description">
              Monitor borrower records and evaluate credit default risk.
            </p>
          </div>
          <button
            className="button button-secondary"
            onClick={async () => {
              setError("");
              setSuccess("");
              try {
                await loadBorrowers();
                if (selectedBorrowerId) {
                  await loadAssessments(selectedBorrowerId);
                }
                setSuccess("Dashboard refreshed.");
              } catch (err) {
                setError(err.message);
              }
            }}
          >
            ↻ Refresh
          </button>
        </header>

        {error && (
          <div className="alert alert-error" role="alert">
            <span>{error}</span>
            <button
              className="alert-dismiss"
              onClick={() => setError("")}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {success && (
          <div className="alert alert-success" role="status">
            <span>{success}</span>
            <button
              className="alert-dismiss"
              onClick={() => setSuccess("")}
              aria-label="Dismiss message"
            >
              ×
            </button>
          </div>
        )}

        {loading && activeView === "Overview" ? (
          <div className="loading-state">Connecting to your database…</div>
        ) : (
          <>
            {activeView === "Overview" && renderOverview()}
            {activeView === "Borrowers" && renderBorrowers()}
            {activeView === "Risk assessment" && renderAssessmentForm()}
            {activeView === "Assessment history" && renderHistory()}
          </>
        )}

        <footer className="result-disclaimer">
          Credit Risk Scoring Demo · Predictions are experimental and should
          not be used as the sole basis for credit decisions.
        </footer>
      </main>
    </div>
  );
}
