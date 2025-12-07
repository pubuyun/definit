import React from "react";
import Input from "@mui/joy/Input";
import IconButton from "@mui/joy/IconButton";
import Box from "@mui/joy/Box";
import SearchIcon from "@mui/icons-material/Search";

const SearchBar = ({ onSearch }) => {
    const [query, setQuery] = React.useState("");

    const handleSearch = () => {
        if (onSearch) {
            onSearch(query);
        }
    };

    return (
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Input
                placeholder="Search..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                variant="outlined"
                size="md"
                onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        handleSearch();
                    }
                }}
                sx={{ flexGrow: 1 }}
            />
            <IconButton onClick={handleSearch} variant="solid" color="primary">
                <SearchIcon />
            </IconButton>
        </Box>
    );
};

export default SearchBar;
