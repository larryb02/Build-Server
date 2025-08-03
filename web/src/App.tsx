import Header from './Header'
import Dashboard from './Dashboard';

import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

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
      <Dashboard/>
    </ThemeProvider>
  )
}

export default App
