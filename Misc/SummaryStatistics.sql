/* Count of records with browser trusted certificates */
SELECT doc.run_date as RunDate, COUNT(*) as CountBrowserTrusted
	FROM records-fresh-ie-* 
	WHERE doc.p443.data.http.response.request.tls_handshake.server_certificates.validation.browser_trusted=true 
	GROUP BY doc.run_date;

SELECT doc.p443.data.http.response.request.tls_handshake.server_hello.cipher_suite.name as CipherSuite,
			COUNT(*)
	FROM records-fresh-ie-*
	GROUP BY doc.run_date;