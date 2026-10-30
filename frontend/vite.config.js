import {defineConfig} from 'vite';
const target=process.env.ROOM_API_TARGET||'http://127.0.0.1:8000';
export default defineConfig({server:{host:'0.0.0.0',proxy:{'/api':target,'/media':target,'/health':target}},preview:{host:'0.0.0.0'}});
