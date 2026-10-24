// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IntegrityContract {

    mapping(string => string) private recordHashes;

    function storeHash(
        string memory recordId,
        string memory dataHash
    ) public {
        recordHashes[recordId] = dataHash;
    }

    function getHash(
        string memory recordId
    ) public view returns (string memory) {
        return recordHashes[recordId];
    }
}