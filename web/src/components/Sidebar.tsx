import { NavLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import DirectionsRunIcon from '@mui/icons-material/DirectionsRun';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import FolderIcon from '@mui/icons-material/Folder';
import TerminalIcon from '@mui/icons-material/Terminal';

const DRAWER_WIDTH = 260;

const navItems = [
    { label: 'Projects',  path: '/',          icon: <FolderIcon /> },
    { label: 'Pipelines', path: '/pipelines', icon: <AccountTreeIcon /> },
    { label: 'Runners',   path: '/runners',   icon: <DirectionsRunIcon /> },
];

export default function Sidebar() {
    return (
        <Drawer
            variant="permanent"
            sx={{
                width: DRAWER_WIDTH,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                    width: DRAWER_WIDTH,
                    boxSizing: 'border-box',
                    borderRight: '1px solid',
                    borderColor: 'divider',
                },
            }}
        >
            <Box sx={{ px: 3, py: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <TerminalIcon color="primary" />
                <Typography variant="h6" fontWeight={700} noWrap>
                    Build Server
                </Typography>
            </Box>
            <Divider />
            <List sx={{ px: 1.5, pt: 2 }}>
                {navItems.map(({ label, path, icon }) => (
                    <ListItem key={label} disablePadding sx={{ mb: 0.5 }}>
                        <ListItemButton
                            component={NavLink}
                            to={path}
                            end={path === '/'}
                            sx={{
                                borderRadius: 2,
                                '&.active': {
                                    bgcolor: 'primary.main',
                                    color: 'white',
                                    '& .MuiListItemIcon-root': { color: 'white' },
                                },
                            }}
                        >
                            <ListItemIcon sx={{ minWidth: 40 }}>{icon}</ListItemIcon>
                            <ListItemText primary={label} />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
        </Drawer>
    );
}
