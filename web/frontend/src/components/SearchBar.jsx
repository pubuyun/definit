import React from "react";
import TextField from "@mui/joy/TextField";
import IconButton from "@mui/joy/IconButton";
import SearchIcon from "@mui/icons-material/Search";

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = React.useState("");

  const handleSearch = () => {
    if (onSearch) {
      onSearch(query);
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <TextField
        placeholder="Search..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        variant="outlined"
        size="md"
        sx={{ flexGrow: 1 }}
      />
      <IconButton onClick={handleSearch} variant="solid" color="primary">
        <SearchIcon />
      </IconButton>
    </div>
  );
};

export default SearchBar;
