import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

import Sidebar from './components/Sidebar';
import Projects from './views/Projects';
import Pipelines from './views/Pipelines';
import PipelineDetail from './views/PipelineDetail';
import Runners from './views/Runners';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
  typography: {
    fontSize: 16,
  },
  spacing: 10,
});

export default function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Sidebar />
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
            {/* <Header /> */}
            <Box component="main" sx={{ flexGrow: 1, p: 4, overflow: 'auto' }}>
              <Routes>
                <Route path="/" element={<Projects />} />
                <Route path="/pipelines" element={<Pipelines />} />
                <Route path="/pipelines/:id" element={<PipelineDetail />} />
                <Route path="/runners" element={<Runners />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}
