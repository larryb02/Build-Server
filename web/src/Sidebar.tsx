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
import WorkIcon from '@mui/icons-material/Work';

const DRAWER_WIDTH = 220;

const navItems = [
    { label: 'Jobs', path: '/', icon: <WorkIcon /> },
    { label: 'Runners', path: '/runners', icon: <DirectionsRunIcon /> },
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
                },
            }}
        >
            <Box sx={{ px: 2, py: 2 }}>
                <Typography variant="h6" noWrap>
                    Build Server
                </Typography>
            </Box>
            <Divider />
            <List>
                {navItems.map(({ label, path, icon }) => (
                    <ListItem key={label} disablePadding>
                        <ListItemButton
                            component={NavLink}
                            to={path}
                            end={path === '/'}
                            sx={{
                                '&.active': {
                                    bgcolor: 'action.selected',
                                },
                            }}
                        >
                            <ListItemIcon>{icon}</ListItemIcon>
                            <ListItemText primary={label} />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
        </Drawer>
    );
}
