
import { useEffect, useState } from "react";
import axios from "axios";
import {
  Activity, BriefcaseBusiness, CircleAlert, Clock3, Gauge,
  RefreshCw, Search, ShieldCheck, Users, X
} from "lucide-react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const initialFeatures = {
  limit_bal: 50000,
  pay_status_sep: 2,
  pay_status_aug: 2,
  pay_status_jul: 1,
  pay_status_jun: 1,
  pay_status_may: 0,
  pay_status_apr: 0,
  bill_amt1: 45000,
  bill_amt2: 42000,
  bill_amt3: 40000,
  bill_amt4: 38000,
  bill_amt5: 35000,
  bill_amt6: 32000,
  pay_amt1: 0,
  pay_amt2: 1000,
  pay_amt3: 2000,
  pay_amt4: 3000,
  pay_amt5: 3000,
  pay_amt6: 4000,
};

function App() {
  const [borrowers, setBorrowers] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [history, setHistory] = useState([]);
  const [features, setFeatures] = useState(initialFeatures);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [newReference, setNewReference] = useState("");

  async function loadBorrowers() {
    setError("");
    try {
      const response = await axios.get(`${API}/borrowers`);
      setBorrowers(response.data);
      setSelectedId((current) => {
        if (current && response.data.some((b) => String(b.borrower_id) === current)) return current;
        return response.data.length ? String(response.data[0].borrower_id) : "";
      });
    } catch {
      setError("Couldn't connect to the API. Check that FastAPI is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory(id) {
    if (!id) {
      setHistory([]);
      return;
    }
    try {
      const response = await axios.get(`${API}/borrowers/${id}/assessments`);
      setHistory(response.data);
    } catch {
      setHistory([]);
    }
  }

  useEffect(() => {
    loadBorrowers();
  }, []);

  useEffect(() => {
    setResult(null);
    loadHistory(selectedId);
  }, [selectedId]);

  async function addBorrower(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await axios.post(`${API}/borrowers`, {
        full_name: newName.trim(),
        managed_by: 1,
        external_reference: newReference.trim() || null,
      });
      await loadBorrowers();
      setSelectedId(String(response.data.borrower_id));
      setNewName("");
      setNewReference("");
      setShowAdd(false);
      setNotice("Borrower added successfully.");
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't create borrower. Check analyst user ID 1 exists and the reference is unique.");
    } finally {
      setBusy(false);
    }
  }

  async function assess(event) {
    event.preventDefault();
    if (!selectedId) {
      setError("Add or select a borrower before running an assessment.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const payload = Object.fromEntries(
        Object.entries(features).map(([key, value]) => [key, Number(value)])
      );
      const response = await axios.post(`${API}/borrowers/${selectedId}/assess`, payload);
      setResult(response.data);
      setNotice("Risk assessment completed and saved.");
      await loadHistory(selectedId);
    } catch (err) {
      setError(err.response?.data?.detail || "Assessment failed. Check the API and the supplied values.");
    } finally {
      setBusy(false);
    }
  }

  const filtered = borrowers.filter((b) =>
    `${b.full_name} ${b.external_reference || ""}`.toLowerCase().includes(search.toLowerCase())
  );
  const latest = history[0];
  const higherCount = history.filter((a) => a.risk_category === "higher").length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={23} /></div>
          <div><strong>Credence</strong><span>RISK INTELLIGENCE</span></div>
        </div>
        <div className="side-label">WORKSPACE</div>
        <a className="nav-link active" href="#overview"><Gauge size={18} /> Overview</a>
        <a className="nav-link" href="#borrowers"><Users size={18} /> Borrowers</a>
        <a className="nav-link" href="#assessment"><Activity size={18} /> Risk assessment</a>
        <a className="nav-link" href="#history"><Clock3 size={18} /> Assessment history</a>
        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div><strong>Development mode</strong><span>Local API connection</span></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">CREDIT INTELLIGENCE / OVERVIEW</div>
            <h1>Risk dashboard</h1>
            <p className="subheading">Monitor borrowers and run experimental credit risk assessments.</p>
          </div>
          <button className="button secondary" onClick={loadBorrowers}><RefreshCw size={16} /> Refresh</button>
        </header>

        {error && <div className="message error"><CircleAlert size={18} /> {error}<button onClick={() => setError("")}><X size={16}/></button></div>}
        {notice && <div className="message success"><ShieldCheck size={18} /> {notice}<button onClick={() => setNotice("")}><X size={16}/></button></div>}

        <section className="stats-grid" id="overview">
          <article className="stat-card">
            <div className="stat-top"><span>Total borrowers</span><div className="stat-icon blue"><Users size={19}/></div></div>
            <div className="stat-value">{borrowers.length}</div><div className="stat-foot">Registered in the database</div>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Assessments saved</span><div className="stat-icon purple"><Activity size={19}/></div></div>
            <div className="stat-value">{history.length}</div><div className="stat-foot">For the selected borrower</div>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Latest risk score</span><div className="stat-icon amber"><Gauge size={19}/></div></div>
            <div className="stat-value">{latest ? `${latest.risk_score}/100` : "—"}</div><div className="stat-foot">{latest ? `${latest.risk_category} risk category` : "No assessment yet"}</div>
          </article>
          <article className="stat-card">
            <div className="stat-top"><span>Higher-risk assessments</span><div className="stat-icon red"><CircleAlert size={19}/></div></div>
            <div className="stat-value">{higherCount}</div><div className="stat-foot">For the selected borrower</div>
          </article>
        </section>

        <section className="panel" id="borrowers">
          <div className="panel-header">
            <div><h2>Borrowers</h2><p>Choose a borrower to view history or assess risk.</p></div>
            <button className="button primary" onClick={() => setShowAdd(!showAdd)}>
              {showAdd ? <X size={16}/> : <Users size={16}/>} {showAdd ? "Cancel" : "Add borrower"}
            </button>
          </div>

          {showAdd && <form className="add-form" onSubmit={addBorrower}>
            <label>Full name<input value={newName} onChange={(e) => setNewName(e.target.value)} required maxLength={150} placeholder="e.g. Aditi Sharma"/></label>
            <label>External reference <span className="optional">(optional)</span><input value={newReference} onChange={(e) => setNewReference(e.target.value)} maxLength={50} placeholder="e.g. BRW-002"/></label>
            <button className="button primary" disabled={busy}>{busy ? "Saving…" : "Save borrower"}</button>
          </form>}

          <div className="table-tools">
            <div className="search-box"><Search size={17}/><input placeholder="Search borrowers..." value={search} onChange={(e) => setSearch(e.target.value)}/></div>
            <span className="record-count">{filtered.length} records</span>
          </div>

          <div className="table-wrap"><table>
            <thead><tr><th>Borrower</th><th>Reference</th><th>Latest risk</th><th>Category</th><th>Action</th></tr></thead>
            <tbody>
              {loading ? <tr><td colSpan="5" className="empty">Loading borrowers…</td></tr> :
                filtered.map((b) => <tr key={b.borrower_id} className={String(b.borrower_id) === selectedId ? "selected-row" : ""}>
                  <td><div className="person-cell"><div className="avatar">{b.full_name?.charAt(0)?.toUpperCase() || "B"}</div><div><strong>{b.full_name}</strong><span>ID #{b.borrower_id}</span></div></div></td>
                  <td>{b.external_reference || "—"}</td>
                  <td>{String(b.borrower_id) === selectedId && latest ? `${latest.risk_score}/100` : "—"}</td>
                  <td>{String(b.borrower_id) === selectedId && latest ? <span className={`risk-pill ${latest.risk_category}`}>{latest.risk_category}</span> : <span className="muted">Not assessed</span>}</td>
                  <td><button className="text-button" onClick={() => setSelectedId(String(b.borrower_id))}>{String(b.borrower_id) === selectedId ? "Selected" : "View / assess"}</button></td>
                </tr>)}
              {!loading && filtered.length === 0 && <tr><td colSpan="5" className="empty">No borrowers found. Add one to get started.</td></tr>}
            </tbody>
          </table></div>
        </section>

        <section className="panel" id="assessment">
          <div className="panel-header">
            <div><h2>Run a risk assessment</h2><p>Enter credit-card repayment and balance features for the selected borrower.</p></div>
            <span className="model-badge"><span/> Random Forest · v1.0</span>
          </div>
          <form onSubmit={assess}>
            <div className="selected-borrower">
              <label>Selected borrower<select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} required>
                <option value="">Select a borrower</option>
                {borrowers.map((b) => <option key={b.borrower_id} value={b.borrower_id}>{b.full_name} · #{b.borrower_id}</option>)}
              </select></label>
              <div className="feature-note"><BriefcaseBusiness size={17}/> 19 model features required</div>
            </div>

            <div className="feature-section">
              <h3>Credit limit & repayment status</h3>
              <p>Repayment status values should follow the dataset's original coding.</p>
              <div className="feature-grid">
                {["limit_bal", "pay_status_sep", "pay_status_aug", "pay_status_jul", "pay_status_jun", "pay_status_may", "pay_status_apr"].map((key) =>
                  <label key={key}>{key}<input type="number" step={key.startsWith("pay_status") ? "1" : "any"} required value={features[key]} onChange={(e) => setFeatures({...features, [key]: e.target.value})}/></label>
                )}
              </div>
            </div>

            <div className="feature-section"><h3>Bill amounts</h3><div className="feature-grid six">
              {["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"].map((key) =>
                <label key={key}>{key}<input type="number" step="any" required value={features[key]} onChange={(e) => setFeatures({...features, [key]: e.target.value})}/></label>
              )}
            </div></div>

            <div className="feature-section"><h3>Previous payment amounts</h3><div className="feature-grid six">
              {["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"].map((key) =>
                <label key={key}>{key}<input type="number" step="any" required value={features[key]} onChange={(e) => setFeatures({...features, [key]: e.target.value})}/></label>
              )}
            </div></div>

            <div className="form-footer"><span>Assessment is saved to PostgreSQL.</span><button className="button primary large" disabled={busy || !selectedId}><Activity size={17}/>{busy ? "Assessing…" : "Generate risk assessment"}</button></div>
          </form>

          {result && <div className="result-card">
            <div className="result-heading"><div><span className="eyebrow">LATEST MODEL OUTPUT</span><h3>Assessment #{result.assessment_id}</h3></div><span className={`risk-pill ${result.risk_category}`}>{result.risk_category} risk</span></div>
            <div className="result-grid">
              <div><span>Risk score</span><strong>{result.risk_score}<small>/100</small></strong></div>
              <div><span>Model output (uncalibrated)</span><strong>{(result.default_probability * 100).toFixed(2)}<small>%</small></strong></div>
              <div><span>Classification at 0.45 threshold</span><strong>{result.predicted_default ? "Default flag: Yes" : "Default flag: No"}</strong></div>
            </div>
            <p className="caveat">Prototype only: this model uses historical Taiwanese credit-card data. Its outputs are not validated for Indian lending and should not be used for real credit decisions.</p>
          </div>}
        </section>

        <section className="panel" id="history">
          <div className="panel-header"><div><h2>Assessment history</h2><p>Saved model outputs for the selected borrower.</p></div><span className="record-count">{history.length} assessments</span></div>
          <div className="table-wrap"><table>
            <thead><tr><th>Assessment</th><th>Score</th><th>Model output</th><th>Category</th><th>Model</th><th>Assessed at</th></tr></thead>
            <tbody>
              {history.map((a) => <tr key={a.assessment_id}>
                <td>#{a.assessment_id}</td><td><strong>{a.risk_score}/100</strong></td>
                <td>{(Number(a.default_probability) * 100).toFixed(2)}%</td>
                <td><span className={`risk-pill ${a.risk_category}`}>{a.risk_category}</span></td>
                <td>{a.model_name} <span className="muted">v{a.model_version}</span></td>
                <td>{a.assessed_at ? new Date(a.assessed_at).toLocaleString() : "—"}</td>
              </tr>)}
              {history.length === 0 && <tr><td colSpan="6" className="empty">No assessments for this borrower yet.</td></tr>}
            </tbody>
          </table></div>
        </section>

        <footer className="page-footer"><span>Credence · Dynamic Credit Risk Scoring</span><span><span className="live-dot"/> Local development environment</span></footer>
      </main>
    </div>
  );
}

export default App;
