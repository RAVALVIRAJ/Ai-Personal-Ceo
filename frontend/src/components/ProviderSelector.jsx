// ProviderSelector.jsx – shows a dropdown of available LLM providers and persists the choice in localStorage.
import { useEffect, useState } from "react";
import { getOptions } from "../services/aiApi";

const ProviderSelector = () => {
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState(() => localStorage.getItem("selectedProvider") || "");

  // Fetch available providers on mount
  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await getOptions();
        const list = data.providers || [];
        setProviders(list);
        if (!selected && list.length) {
          const defaultProv = list[0];
          setSelected(defaultProv);
          localStorage.setItem("selectedProvider", defaultProv);
        }
      } catch (e) {
        console.error("Failed to fetch LLM options", e);
      }
    };
    fetch();
  }, []);

  const handleChange = (e) => {
    const value = e.target.value;
    setSelected(value);
    localStorage.setItem("selectedProvider", value);
  };

  if (providers.length < 2) return null;

  return (
    <div className="provider-selector">
      <label htmlFor="provider-select">LLM Provider: </label>
      <select id="provider-select" value={selected} onChange={handleChange}>
        {providers.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ProviderSelector;
