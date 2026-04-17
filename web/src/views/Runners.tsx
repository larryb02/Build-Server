import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

import { useEffect, useState } from 'react';
import config from '../config';

type Runner = {
    runner_id: number;
    name: string;
    health: string;
    last_seen: string;
};

type ChipColor = 'success' | 'error' | 'warning' | 'default';

function healthChip(health: string) {
    const map: Record<string, { color: ChipColor; label: string }> = {
        HEALTHY:   { color: 'success', label: 'Healthy' },
        UNHEALTHY: { color: 'error',   label: 'Unhealthy' },
        OFFLINE:   { color: 'warning', label: 'Offline' },
    };
    const h = map[health] ?? { color: 'default', label: health };
    return <Chip label={h.label} color={h.color} size="small" />;
}

type TokenDialog = {
    open: boolean;
    token: string | null;
    error: string | null;
    loading: boolean;
};

const TOKEN_CLOSED: TokenDialog = { open: false, token: null, error: null, loading: false };

export default function Runners() {
    const [runners, setRunners] = useState<Runner[]>([]);
    const [fetchError, setFetchError] = useState(false);
    const [tokenDialog, setTokenDialog] = useState<TokenDialog>(TOKEN_CLOSED);

    const fetchRunners = async () => {
        try {
            const res = await fetch(config.routes.runners);
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            setRunners(await res.json());
        } catch (err) {
            console.error(`${err}`);
            setFetchError(true);
        }
    };

    useEffect(() => { fetchRunners(); }, []);

    const openTokenDialog = async () => {
        setTokenDialog({ open: true, token: null, error: null, loading: true });
        try {
            const res = await fetch(config.routes.runnersToken, { method: 'POST' });
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            const body = await res.json();
            setTokenDialog((prev) => ({ ...prev, loading: false, token: body.token }));
        } catch (err) {
            setTokenDialog((prev) => ({ ...prev, loading: false, error: `${err}` }));
        }
    };

    const handleDelete = async (runner: Runner) => {
        try {
            const res = await fetch(`${config.routes.runners}/${runner.runner_id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            await fetchRunners();
        } catch (err) {
            console.error(`${err}`);
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5" sx={{ flexGrow: 1 }}>Runners</Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openTokenDialog}>
                    Add Runner
                </Button>
            </Box>

            {fetchError && <Alert severity="error" sx={{ mb: 2 }}>Something went wrong — could not load runners.</Alert>}

            <TableContainer component={Paper} sx={{ flexGrow: 1, overflow: 'auto' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Health</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {runners.map((row) => (
                            <TableRow
                                key={row.runner_id}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell>{row.name}</TableCell>
                                <TableCell>{healthChip(row.health)}</TableCell>
                                <TableCell>
                                    <Tooltip title="Delete runner">
                                        <IconButton size="small" onClick={() => handleDelete(row)}>
                                            <DeleteOutlineIcon fontSize="small" />
                                        </IconButton>
                                    </Tooltip>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Add runner / token dialog */}
            <Dialog open={tokenDialog.open} onClose={() => setTokenDialog(TOKEN_CLOSED)} fullWidth maxWidth="sm">
                <DialogTitle>Add Runner</DialogTitle>
                <DialogContent>
                    {tokenDialog.loading && (
                        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                            <CircularProgress />
                        </Box>
                    )}
                    {tokenDialog.error && (
                        <Alert severity="error">{tokenDialog.error}</Alert>
                    )}
                    {tokenDialog.token && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                Run the following command on your runner machine to register it with this server:
                            </Typography>
                            <Box
                                sx={{
                                    bgcolor: 'grey.900',
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    borderRadius: 1,
                                    px: 2,
                                    py: 1.5,
                                    fontFamily: 'monospace',
                                    fontSize: '0.85rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-all',
                                    color: 'success.light',
                                }}
                            >
                                {`buildserver-runner register --url <SERVER_URL> --token ${tokenDialog.token} --name <RUNNER_NAME>`}
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                                This token expires after 1 hour and can only be used once.
                            </Typography>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setTokenDialog(TOKEN_CLOSED)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
