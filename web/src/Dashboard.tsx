import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';

import { useEffect, useState } from 'react';
import { TableFooter } from '@mui/material';

import config from './config';

export default function Dashboard() {
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(5);
    const [builds, setBuilds] = useState([]);

    useEffect(() => {
        const fetchBuilds = async () => {
            try {
                const res = await fetch(`${config.API_HOSTNAME}builds/`);
                const json = await res.json();
                setBuilds(json);
            } catch (error) {
                console.error(`Failed to fetch ${error}`);
            }
        }
        fetchBuilds();
    }, [])

    const handleChangePage = (
        event: React.MouseEvent<HTMLButtonElement> | null,
        newPage: number,
    ) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (
        event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    ) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    return (
        <Box sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
        }}>
            <TableContainer component={Paper}>
                <Table sx={{ minWidth: 650 }} aria-label="simple table">
                    <TableHead>
                        <TableRow>
                            <TableCell>Repository</TableCell>
                            <TableCell align="left">Commit</TableCell>
                            <TableCell align="left">Status</TableCell>
                            {/* <TableCell align="left">Built At</TableCell> */}
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
                                {/* <TableCell align="left">{row.created_at}</TableCell> */}
                            </TableRow>
                        ))}
                    </TableBody>
                    <TableFooter>
                        <TableRow>
                            <TablePagination rowsPerPageOptions={[5, 10, { label: 'All', value: -1 }]}
                                page={page}
                                colSpan={3}
                                count={builds.length}
                                rowsPerPage={rowsPerPage}
                                slotProps={{
                                    select: {
                                        inputProps: {
                                            'aria-label': 'rows per page',
                                        },
                                        native: true,
                                    },
                                }}
                                onPageChange={handleChangePage}
                                onRowsPerPageChange={handleChangeRowsPerPage}
                            />
                        </TableRow>
                    </TableFooter>
                </Table>
            </TableContainer>
        </Box>
    );
}