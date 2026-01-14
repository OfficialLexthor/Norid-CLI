# EPP server – Norid
Norid’s registration system consists of a database and an interface registrars use to enter and update data in the database. We use the communication protocol EPP for the interface. EPP is a standard protocol used by a majority of registration services world-wide.

[About the EPP protocol](https://en.wikipedia.org/wiki/Extensible_Provisioning_Protocol)

Access
------

The EPP-server is available at:

```
Host: epp.norid.no
Port: 700 (TLS)
```


You need an account to access the EPP server. All registrars have been assigned an EPP account and two test accounts. New registrars are assigned their accounts when the registrar agreement is established.

[Acceptable use policy for Norid's registry system](https://teknisk.norid.no/en/administrere-domenenavn/aup/)

Testing
-------

The host server is available at:

```
Host: epp.test.norid.no
Port: 700  (SSL/TLS)
```


To check if the test server is active, you can use this openssl command:

```
openssl s_client -connect epp.test.norid.no:700
```


You can also use thid telnet-ssl command:

```
telnet-ssl -z ssl epp.test.norid.no 700
```


If the EEP greeting is returned, the connection is successful.

  
Depending on your software, you may need local certificates to connect with the EPP services. [Read more about EPP certificates.](https://teknisk.norid.no/en/integrere-mot-norid/epp/epp-sertifikater/)

[Click here to read more about the most common problems with EPP testing.](https://teknisk.norid.no/en/integrere-mot-norid/test-system/mer-om-testing-av-epp/)

Technical documentation
-----------------------


|Interface, certificates and examples              |
|--------------------------------------------------|
|Documentation of the EPP interface - versjon 1.0.2|
|EPP certificates                                  |
|EPP XML sequence examples                         |
|XML examples of transfer to a new registrar       |
|Constants and system limitations in the EPP system|
|Error messages from the registry system           |
|Database objects and attributes                   |


EPP software
------------

[List of EPP software](https://teknisk.norid.no/en/integrere-mot-norid/epp/epp-programvare/)

Published: 9 July 2014  
Updated: 28 November 2024