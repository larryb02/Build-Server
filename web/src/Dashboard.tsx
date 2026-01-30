import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Container from '@mui/material/Container';

import { useEffect, useState } from 'react';
import config from './config';

type Build = {
    build_id: number,
    git_repository_url: string,
    commit_hash: string,
    build_status: string,
}

export default function Dashboard() {
    const [builds, setBuilds] = useState<Build[]>([]);

    useEffect(() => {
        const fetchBuilds = async () => {
            try {
                const res = await fetch(`${config.API_HOSTNAME}${config.routes.builds}`);
                const json = await res.json();
                setBuilds(json);
            } catch (error) {
                console.error(`Failed to fetch ${error}`);
            }
        }
        fetchBuilds();
    }, [])

    return (
        <Container maxWidth='md' sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        }}>
            <Paper sx={{ height: 600 }} elevation={3}
            >
                <TableContainer sx={{
                    height: '100%',
                    overflowY: 'auto'
                }} component={Paper}>
                    <Table sx={{ minWidth: 650 }} aria-label="simple table">
                        <TableHead>
                            <TableRow>
                                <TableCell >Repository</TableCell>
                                <TableCell align="left">Commit</TableCell>
                                <TableCell align="left">Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {builds.map((row) => (
                                <TableRow
                                    key={row.build_id}
                                    sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                                >
                                    <TableCell component="th" scope="row">
                                        {row.git_repository_url}
                                    </TableCell>
                                    <TableCell align="left">{row.commit_hash}</TableCell>
                                    <TableCell align="left">{row.build_status}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Container>
    );
}
