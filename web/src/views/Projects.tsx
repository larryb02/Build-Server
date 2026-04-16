import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import AddIcon from '@mui/icons-material/Add';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

import { useEffect, useState } from 'react';
import config from '../config';

type Project = {
    project_id: number;
    name: string;
    git_repository_url: string;
    created_at: string;
};

type AddDialog = {
    open: boolean;
    name: string;
    url: string;
    error: string | null;
    loading: boolean;
};

type TriggerDialog = {
    project: Project | null;
    branch: string;
    error: string | null;
    loading: boolean;
};

type RowMenu = {
    project: Project | null;
    anchor: HTMLElement | null;
};

const ADD_CLOSED: AddDialog = { open: false, name: '', url: '', error: null, loading: false };
const TRIGGER_CLOSED: TriggerDialog = { project: null, branch: 'main', error: null, loading: false };
const MENU_CLOSED: RowMenu = { project: null, anchor: null };

export default function Projects() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [fetchError, setFetchError] = useState(false);
    const [add, setAdd] = useState<AddDialog>(ADD_CLOSED);
    const [trigger, setTrigger] = useState<TriggerDialog>(TRIGGER_CLOSED);
    const [rowMenu, setRowMenu] = useState<RowMenu>(MENU_CLOSED);

    const fetchProjects = async () => {
        try {
            const res = await fetch(config.routes.projects);
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            setProjects(await res.json());
        } catch (err) {
            console.error(`${err}`);
            setFetchError(true);
        }
    };

    useEffect(() => { fetchProjects(); }, []);

    const handleAdd = async () => {
        setAdd((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const res = await fetch(config.routes.projects, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: add.name, git_repository_url: add.url }),
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
            }
            setAdd(ADD_CLOSED);
            await fetchProjects();
        } catch (err) {
            setAdd((prev) => ({ ...prev, loading: false, error: `${err}` }));
        }
    };

    const handleTrigger = async () => {
        if (!trigger.project) return;
        setTrigger((prev) => ({ ...prev, loading: true, error: null }));
        try {
            const res = await fetch(
                `${config.routes.projects}/${trigger.project.project_id}/trigger`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ branch: trigger.branch }),
                }
            );
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
            }
            setTrigger(TRIGGER_CLOSED);
        } catch (err) {
            setTrigger((prev) => ({ ...prev, loading: false, error: `${err}` }));
        }
    };

    const openTrigger = () => {
        const project = rowMenu.project;
        setRowMenu(MENU_CLOSED);
        if (project) setTrigger({ ...TRIGGER_CLOSED, project });
    };

    const handleDelete = async () => {
        const project = rowMenu.project;
        setRowMenu(MENU_CLOSED);
        if (!project) return;
        try {
            const res = await fetch(`${config.routes.projects}/${project.project_id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            await fetchProjects();
        } catch (err) {
            console.error(`${err}`);
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5" sx={{ flexGrow: 1 }}>Projects</Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setAdd({ ...ADD_CLOSED, open: true })}
                >
                    Add Project
                </Button>
            </Box>

            {fetchError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    Something went wrong — could not load projects.
                </Alert>
            )}

            <TableContainer component={Paper} sx={{ flexGrow: 1, overflow: 'auto' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Repository</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {projects.map((row) => (
                            <TableRow
                                key={row.project_id}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell>{row.name}</TableCell>
                                <TableCell sx={{ fontFamily: 'monospace' }}>{row.git_repository_url}</TableCell>
                                <TableCell>
                                    <IconButton
                                        size="small"
                                        onClick={(e) => setRowMenu({ project: row, anchor: e.currentTarget })}
                                    >
                                        <MoreVertIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Row actions menu */}
            <Menu
                anchorEl={rowMenu.anchor}
                open={!!rowMenu.anchor}
                onClose={() => setRowMenu(MENU_CLOSED)}
            >
                <MenuItem disabled>
                    <ListItemIcon><InfoOutlinedIcon fontSize="small" /></ListItemIcon>
                    <ListItemText>Details</ListItemText>
                </MenuItem>
                <MenuItem onClick={openTrigger}>
                    <ListItemIcon><PlayArrowIcon fontSize="small" /></ListItemIcon>
                    <ListItemText>Trigger Pipeline</ListItemText>
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleDelete}>
                    <ListItemIcon><DeleteOutlineIcon fontSize="small" /></ListItemIcon>
                    <ListItemText>Delete</ListItemText>
                </MenuItem>
            </Menu>

            {/* Add project dialog */}
            <Dialog open={add.open} onClose={() => setAdd(ADD_CLOSED)} fullWidth maxWidth="sm">
                <DialogTitle>Add Project</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
                    {add.error && <Alert severity="error">{add.error}</Alert>}
                    <TextField
                        label="Name"
                        value={add.name}
                        onChange={(e) => setAdd((prev) => ({ ...prev, name: e.target.value }))}
                        fullWidth
                    />
                    <TextField
                        label="Git Repository URL"
                        value={add.url}
                        onChange={(e) => setAdd((prev) => ({ ...prev, url: e.target.value }))}
                        fullWidth
                        placeholder="https://github.com/user/repo.git"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAdd(ADD_CLOSED)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={handleAdd}
                        disabled={add.loading || !add.name.trim() || !add.url.trim()}
                    >
                        {add.loading ? 'Adding…' : 'Add'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Trigger pipeline dialog */}
            <Dialog open={!!trigger.project} onClose={() => setTrigger(TRIGGER_CLOSED)} fullWidth maxWidth="xs">
                <DialogTitle>Trigger Pipeline — {trigger.project?.name}</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
                    {trigger.error && <Alert severity="error">{trigger.error}</Alert>}
                    <TextField
                        label="Branch"
                        value={trigger.branch}
                        onChange={(e) => setTrigger((prev) => ({ ...prev, branch: e.target.value }))}
                        fullWidth
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setTrigger(TRIGGER_CLOSED)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={handleTrigger}
                        disabled={trigger.loading || !trigger.branch.trim()}
                    >
                        {trigger.loading ? 'Triggering…' : 'Trigger'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
