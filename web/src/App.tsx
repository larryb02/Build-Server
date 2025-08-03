import Header from './Header'
import Dashboard from './Dashboard';

import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});
function App() {

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Header />
      <Box sx={{
        height: '100vh',
        width: '100vw',
        display: 'flex'
      }}>
        <Dashboard />
      </Box>
    </ThemeProvider>
  )
}

export default App
