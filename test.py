/* White panel only for top 350px */
div[class*="my-container"]::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 350px;
  background: white;
  z-index: 0;
}

div[class*="my-container"] > * {
  position: relative;
  z-index: 1;
}
