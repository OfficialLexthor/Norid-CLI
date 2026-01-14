# DAS service – Norid
*   [Integrate with Norid](https://teknisk.norid.no/en/integrere-mot-norid/) /  
*   DAS service 

DAS is an acronym for _Domain Availability Service_. In Norwegian, this service is called _Finn ledig domenenavn_.

This is a service where anyone can look up a domain name and see if it is available for registration. A request will yield one of three possible results:

*   The domain name is available for registration.
*   The domain name is already registered.
*   The domain name cannot be registered.

Access
------

The service is available at:

```
Host: finger.norid.no
Port: 79
```


For the web proxy, go to [Find an available domain name](https://www.norid.no/en/domeneoppslag/finn-ledig-domenenavn/). Rate limiting applies.

Testing
-------

The test service is available at:

```
Host: finger.test.norid.no
Port: 79
```


Example of use (requires that you have a finger client installed):

```
finger domain.no@finger.test.norid.no
```


Will indicate whether or not the domain domain.no is registered.

Same example, now in a whois client that connects to port 79:

```
whois -p 79 -h finger.test.norid.no domain.no
```


If you are looking up an IDN domain, you must use whois UTF-8 syntax to specify a UTF-8 character set:

```
whois -p 79 -h finger.test.norid.no -- -c utf-8 ole-žóòôöšŧüžon-æøå.no
```


Technical documentation
-----------------------



* Interface document for whois and DAS: Updated:2018-08-10: Rev. 10e1 with adjusted pretext, see Document History for description.2018-05-23: Rev. 9e1 for new data model and GDPR, see Document History for description.
* Interface document for whois and DAS: Description:This document describes the interface for both whois and DAS.
* Interface document for whois and DAS: Document:Download Whois DAS Interface Specification v10e1 (PDF, 220KB)


Published: 8 July 2020  
Updated: 17 February 2021