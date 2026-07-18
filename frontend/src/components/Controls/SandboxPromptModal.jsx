import { useState } from 'react';

const SandboxPromptModal = ({ onSubmit, onCancel }) => {
  const [newsFeed, setNewsFeed] = useState('');

  const handleSubmit = () => {
    if (newsFeed.trim()) {
      onSubmit(newsFeed.trim());
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <h3>Enter Sandbox Scenario</h3>
        <p className="modal-subtext">
          Describe a hypothetical geopolitical or supply-chain disruption event to simulate.
        </p>
        <textarea
          className="modal-textarea"
          rows={5}
          placeholder="e.g. Houthi rebels have escalated drone strikes near the Bab el-Mandeb strait, forcing several VLCC tankers bound for Fujairah to divert..."
          value={newsFeed}
          onChange={(e) => setNewsFeed(e.target.value)}
          autoFocus
        />
        <div className="modal-actions">
          <button className="modal-btn cancel" onClick={onCancel}>Cancel</button>
          <button className="modal-btn submit" onClick={handleSubmit} disabled={!newsFeed.trim()}>
            Run Simulation
          </button>
        </div>
      </div>
    </div>
  );
};

export default SandboxPromptModal;
