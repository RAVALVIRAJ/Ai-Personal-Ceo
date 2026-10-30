import { useEffect, useState } from "react";
import { getOptions } from "../services/aiApi";

const PROVIDER_LABELS = {
  ollama: "Ollama (Local)",
  openai: "Cloud (Groq/OpenAI)",
  mock: "Mock",
};

const ProviderSelector = () => {
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState(
    () => localStorage.getItem("selectedProvider") || ""
  );

  useEffect(() => {
    let isMounted = true;

    const fetchOptions = async () => {
      try {
        const data = await getOptions();
        if (!isMounted) return;
        const list = data.providers || [];
        setProviders(list);

        const current = localStorage.getItem("selectedProvider");
        if (list.length > 0) {
          if (!current || !list.includes(current)) {
            setSelected(list[0]);
            localStorage.setItem("selectedProvider", list[0]);
          } else {
            setSelected(current);
          }
        }
      } catch (e) {
        console.error("Failed to fetch LLM options", e);
      }
    };

    fetchOptions();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (e) => {
    const value = e.target.value;
    setSelected(value);
    localStorage.setItem("selectedProvider", value);
  };

  // Only render when 2 or more providers are available
  if (providers.length < 2) return null;

  return (
    <div className="provider-selector" title="Select LLM Provider">
      <label htmlFor="provider-select">Model:</label>
      <select
        id="provider-select"
        value={selected}
        onChange={handleChange}
        aria-label="Select LLM Provider"
      >
        {providers.map((p) => (
          <option key={p} value={p}>
            {PROVIDER_LABELS[p] || p}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ProviderSelector;
