import { BrowserRouter, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnchorTestPage from './pages/AnchorTestPage';
import FormControlsPage from './pages/FormControlsPage';
import DownloadDialogTestPage from './pages/DownloadDialogTestPage';
import UploadDialogTestPage from './pages/UploadDialogTestPage';
import WebDialogTestPage from './pages/WebDialogTestPage';
import TableTestPage from './pages/TableTestPage';
import TableDivTestPage from './pages/TableDivTestPage';
import IframeNestedTestPage from './pages/IframeNestedTestPage';
import ShadowNestedTestPage from './pages/ShadowNestedTestPage';
import KeysClickTestPage from './pages/KeysClickTestPage';
import DragToTestPage from './pages/DragToTestPage';
import CookieTestPage from './pages/CookieTestPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/anchor-test" element={<AnchorTestPage />} />
        <Route path="/form-controls" element={<FormControlsPage />} />
        <Route path="/download-dialog-test" element={<DownloadDialogTestPage />} />
        <Route path="/upload-dialog-test" element={<UploadDialogTestPage />} />
        <Route path="/web-dialog-test" element={<WebDialogTestPage />} />
        <Route path="/table-test" element={<TableTestPage />} />
        <Route path="/table-div-test" element={<TableDivTestPage />} />
        <Route path="/iframe-nested-test" element={<IframeNestedTestPage />} />
        <Route path="/shadow-nested-test" element={<ShadowNestedTestPage />} />
        <Route path="/keys-click-test" element={<KeysClickTestPage />} />
        <Route path="/drag-to-test" element={<DragToTestPage />} />
        <Route path="/cookie-test" element={<CookieTestPage />} />
        <Route path="/sdk-web/cookies" element={<CookieTestPage />} />
      </Routes>
    </BrowserRouter>
  );
}
