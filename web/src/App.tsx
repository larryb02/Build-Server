import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

import Sidebar from './Sidebar';
import Runners from './Runners';
import Jobs from './Jobs';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export default function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Sidebar />
          <Box component="main" sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<Jobs />} />
              <Route path="/runners" element={<Runners />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}
