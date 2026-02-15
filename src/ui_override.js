/**
 * Orthanc Explorer 2 UI Override
 *
 * Intercepts "Send to DICOMWeb server" for azure-dicom and redirects to OAuth endpoint.
 * This makes the standard UI button work transparently with OAuth authentication.
 */

(function() {
    'use strict';

    console.log('[OAuth Plugin] Loading UI override for azure-dicom DICOMWeb integration');

    // Wait for Orthanc Explorer 2 to be ready
    $(document).ready(function() {

        // Intercept DICOMweb send actions
        // OE2 uses Vue.js, so we need to hook into the event system

        // Method 1: Intercept at API level - override the DICOMweb API client
        if (window.axios) {
            const originalPost = window.axios.post;

            window.axios.post = function(url, data, config) {
                // Check if this is a DICOMweb STOW request to azure-dicom
                if (url && url.match(/\/dicom-web\/servers\/azure-dicom\/stow/)) {
                    console.log('[OAuth Plugin] Intercepting azure-dicom STOW request');
                    console.log('[OAuth Plugin] Redirecting to OAuth endpoint');

                    // Redirect to OAuth endpoint
                    const oauthUrl = url.replace('/dicom-web/servers/', '/oauth-dicom-web/servers/');

                    return originalPost.call(this, oauthUrl, data, config)
                        .then(function(response) {
                            console.log('[OAuth Plugin] Successfully sent via OAuth');
                            return response;
                        })
                        .catch(function(error) {
                            console.error('[OAuth Plugin] OAuth send failed:', error);
                            throw error;
                        });
                }

                // For other requests, use original behavior
                return originalPost.apply(this, arguments);
            };

            console.log('[OAuth Plugin] Axios interceptor installed');
        }

        // Method 2: Intercept at fetch level (backup for non-axios requests)
        const originalFetch = window.fetch;

        window.fetch = function(url, options) {
            // Check if this is a DICOMweb STOW request to azure-dicom
            if (typeof url === 'string' && url.match(/\/dicom-web\/servers\/azure-dicom\/stow/)) {
                console.log('[OAuth Plugin] Intercepting azure-dicom STOW fetch request');

                // Redirect to OAuth endpoint
                const oauthUrl = url.replace('/dicom-web/servers/', '/oauth-dicom-web/servers/');

                console.log('[OAuth Plugin] Redirecting to:', oauthUrl);

                return originalFetch.call(this, oauthUrl, options)
                    .then(function(response) {
                        console.log('[OAuth Plugin] Successfully sent via OAuth');
                        return response;
                    })
                    .catch(function(error) {
                        console.error('[OAuth Plugin] OAuth send failed:', error);
                        throw error;
                    });
            }

            // For other requests, use original behavior
            return originalFetch.apply(this, arguments);
        };

        console.log('[OAuth Plugin] Fetch interceptor installed');

        // Add visual indicator that OAuth is active
        setTimeout(function() {
            // Find the DICOMWeb server dropdown if it exists
            const serverSelects = document.querySelectorAll('select, [role="combobox"]');
            serverSelects.forEach(function(select) {
                if (select.value === 'azure-dicom' ||
                    select.textContent.includes('azure-dicom')) {

                    // Add a small badge to indicate OAuth is active
                    const badge = document.createElement('span');
                    badge.textContent = '🔐 OAuth';
                    badge.style.cssText = 'margin-left: 8px; font-size: 0.8em; color: #28a745; font-weight: bold;';
                    badge.title = 'OAuth authentication enabled for Azure DICOM';

                    if (select.parentElement) {
                        select.parentElement.appendChild(badge);
                    }
                }
            });
        }, 1000);

        console.log('[OAuth Plugin] UI override complete - azure-dicom will use OAuth transparently');
    });

})();
