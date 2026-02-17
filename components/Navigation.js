import React from "react";
import { Link } from "react-router-dom";

const Navigation = () => {
  return (
    <nav>
      <ul>
        <li>
          <Link to="/">Home</Link>
        </li>
        <li>
          <Link to="/about">About</Link>
        </li>
        <li>
          <Link to="/services">Services</Link>
        </li>
        <li>
          <Link to="/contact">Contact</Link>
        </li>
        <li>
          Pro Tools
          <ul>
            <li>
              <Link to="/advanced-analytics">Advanced Analytics</Link>
            </li>
            {/* Other submenu items */}
          </ul>
        </li>
      </ul>
    </nav>
  );
};

export default Navigation;