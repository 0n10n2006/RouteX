import { useState, useCallback, useRef, useEffect } from "react";
import axios from "axios";

const API_URL = "https://nominatim.openstreetmap.org";

function SearchBox({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const search = useCallback(
    (value) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (!value || value.length < 2) {
        setResults([]);
        setOpen(false);
        return;
      }
      debounceRef.current = setTimeout(async () => {
        setLoading(true);
        try {
          const res = await axios.get(`${API_URL}/search`, {
            params: {
              q: value,
              format: "json",
              limit: 6,
              addressdetails: 1,
            },
            headers: { "Accept-Language": "en" },
          });
          setResults(res.data || []);
          setOpen(true);
        } catch {
          setResults([]);
        } finally {
          setLoading(false);
        }
      }, 400);
    },
    []
  );

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    search(value);
  };

  const handleSelect = (item) => {
    setQuery(item.display_name.split(",").slice(0, 2).join(", "));
    setOpen(false);
    onSelect({
      latitude: parseFloat(item.lat),
      longitude: parseFloat(item.lon),
      name: item.display_name,
      boundingbox: item.boundingbox,
    });
  };

  return (
    <div className="search-box" ref={wrapperRef}>
      <div className="search-input-wrapper">
        <span className="search-icon">⌕</span>
        <input
          type="text"
          className="search-input"
          placeholder="Search any city or address…"
          value={query}
          onChange={handleChange}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
        {loading && <span className="search-spinner" />}
      </div>

      {open && results.length > 0 && (
        <ul className="search-results">
          {results.map((item) => (
            <li key={item.place_id}>
              <button
                className="search-result-item"
                onClick={() => handleSelect(item)}
              >
                <span className="search-result-type">
                  {item.type === "city" || item.type === "town"
                    ? "🏙"
                    : item.type === "village"
                    ? "🏘"
                    : "📍"}
                </span>
                <span className="search-result-text">
                  {item.display_name.length > 80
                    ? item.display_name.slice(0, 80) + "…"
                    : item.display_name}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default SearchBox;
